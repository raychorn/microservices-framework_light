import os, sys
import re
import socket
import shutil
import logging
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

from concurrent import futures

import boto3
import base64

import mujson as json

__docker_config_json__ = os.path.expanduser('~/.docker/config.json')

__aws_creds_dest__ = os.path.expanduser('~/.aws/credentials')
__aws_creds_src__ = './.aws/credentials'

__aws_config_dest__ = os.path.expanduser('~/.aws/config')
__aws_config_src__ = './.aws/config'

__docker_images__ = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}={{.ID}}']

__docker_containers__ = ['docker', 'ps', '-a', '--format', '{{.Image}}={{.ID}}']

__resolve_docker_issues__ = ['./scripts/resolve-docker-issues.sh']

__docker_hello_world__ = ['docker', 'run', 'hello-world']

__aws_cli_login__ = ['aws ecr get-login --no-include-email --region us-east-2']
__aws_cli_login__ = __aws_cli_login__[0].split()

__aws_cli_ecr_describe_repos__ = ['aws', 'ecr', 'describe-repositories']

__aws_cli_ecr_create_repo__ = ['aws', 'ecr', 'create-repository', '--repository-name', '{}', '--image-scanning-configuration', 'scanOnPush=true']

__docker_tag_cmd__ = 'docker tag {} {}:{}'

__docker_push_cmd__ = 'docker push {}:{}'

__aws_docker_login__cmd__ = 'aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin {}'

__docker_system_prune__ = ['yes | docker system prune -a']

__ignoring_images_like_these__ = ['.amazonaws.com']

__aws_cli__ = 'aws-cli/2.'
__hello_from_docker__ = 'Hello from Docker!'
__no_such_file_or_directory__ = 'No such file or directory'

__docker_pulls__ = './script/pulls.sh'

__aws_docker_login__ = './scripts/aws-docker-login.sh {}'
__expected_aws_docker_login__ = 'Login Succeeded'

production_token = 'production'
development_token = 'development'

is_really_something = lambda s,t:(s is not None) and t(s)
something_greater_than_zero = lambda s:(s > 0)
default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]
is_running_production = lambda : (socket.gethostname() != 'DESKTOP-JJ95ENL')

def get_stream_handler(streamformat="%(asctime)s:%(levelname)s -> %(message)s"):
    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO if (not is_running_production()) else logging.DEBUG)
    stream.setFormatter(logging.Formatter(streamformat))
    return stream

    
def setup_rotating_file_handler(logname, logfile, max_bytes, backup_count):
    assert is_really_something(backup_count, something_greater_than_zero), 'Missing backup_count?'
    assert is_really_something(max_bytes, something_greater_than_zero), 'Missing max_bytes?'
    ch = RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
    l = logging.getLogger(logname)
    l.addHandler(ch)
    return l

base_filename = os.path.splitext(os.path.basename(__file__))[0]

log_filename = '{}{}{}{}{}{}{}_{}.log'.format('logs', os.sep, base_filename, os.sep, production_token if (is_running_production()) else development_token, os.sep, base_filename, default_timestamp(datetime.utcnow()))
log_filename = os.sep.join([os.path.dirname(__file__), log_filename])

if not os.path.exists(os.path.dirname(log_filename)):
    os.makedirs(os.path.dirname(log_filename))

if (os.path.exists(log_filename)):
    os.remove(log_filename)

log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s -> %(message)s')
logging.basicConfig(
    level=logging.DEBUG if (not is_running_production()) else logging.INFO,
    format=log_format,
    filename=(log_filename),
)

logger = setup_rotating_file_handler(base_filename, log_filename, (1024*1024*1024), 10)
logger.addHandler(get_stream_handler())

if (not is_running_production()):
    import shutil
    log_root = os.path.dirname(os.path.dirname(log_filename))
    for p in [production_token, development_token]:
        fp = os.sep.join([log_root, p])
        if (os.path.exists(fp)):
            shutil.rmtree(fp)
        
class SmartDict(dict):
    def __setitem__(self, k, v):
        bucket = self.get(k, [])
        bucket.append(v)
        return super().__setitem__(k, bucket)


name_to_id = SmartDict()
id_to_name = {}

response_vectors = {}

current_aws_creds = {}

response_content = []

ignoring_image_names = [__docker_hello_world__[-1]]

has_been_tagged = lambda name:str(name).find('.amazonaws.com/') > -1

__clean_ecr_command_line_option__ = '--clean-ecr'
__push_ecr_command_line_option__ = '--push-ecr'
__verbose_command_line_option__ = '--verbose'
__single_command_line_option__ = '--single'
__scanOnPush_command_line_option__ = '--scanOnPush'
__timetags_command_line_option__ = '--timetags'


def _formatTimeStr():
    return '%Y-%m-%dT%H:%M:%S'

def utcDelta():
    import datetime, time
    _uts = datetime.datetime.utcfromtimestamp(time.time())
    _ts = datetime.datetime.fromtimestamp(time.time())
    return (_uts - _ts if (_uts > _ts) else _ts - _uts)

def getAsDateTimeStr(value, offset=0,fmt=_formatTimeStr()):
    """ return time as 2004-01-10T00:13:50.000Z """
    import sys,time
    import types
    from datetime import datetime

    if (not isinstance(offset,str)):
        if isinstance(value, (tuple, time.struct_time,)):
            return time.strftime(fmt, value)
        if isinstance(value, (int, float,)):
            secs = time.gmtime(value+offset)
            return time.strftime(fmt, secs)

        if isinstance(value, str):
            try: 
                value = time.strptime(value, fmt)
                return time.strftime(fmt, value)
            except: 
                secs = time.gmtime(time.time()+offset)
                return time.strftime(fmt, secs)
        elif (isinstance(value,datetime)):
            from datetime import timedelta
            if (offset is not None):
                value += timedelta(offset)
            ts = time.strftime(fmt, value.timetuple())
            return ts
# END getAsDateTimeStr

def getFromDateTimeStr(ts,format=_formatTimeStr()):
    from datetime import datetime
    try:
        return datetime.strptime(ts,format)
    except ValueError:
        return datetime.strptime('.'.join(ts.split('.')[0:-1]),format)

def getFromDateStr(ts,format=_formatTimeStr()):
    return getFromDateTimeStr(ts,format=format)

def timeSeconds(month=-1,day=-1,year=-1,format=_formatTimeStr()):
    """ get number of seconds """
    import time, datetime
    fromSecs = datetime.datetime.fromtimestamp(time.time())
    s = getAsDateTimeStr(fromSecs,fmt=format)
    _toks = s.split('T')
    toks = _toks[0].split('-')
    if (month > -1):
        toks[0] = '%02d' % (month)
    if (day > -1):
        toks[1] = '%02d' % (day)
    if (year > -1):
        toks[-1] = '%04d' % (year)
    _toks[0] = '-'.join(toks)
    s = 'T'.join(_toks)
    fromSecs = getFromDateStr(s,format=format)
    return time.mktime(fromSecs.timetuple())

def timeStamp(tsecs=0,offset=0,use_iso=False,format=_formatTimeStr(),useLocalTime=True):
    """ get standard timestamp """
    import time
    from datetime import datetime
    secs = 0 if (not useLocalTime) else -utcDelta().seconds
    tsecs = tsecs if (tsecs > 0) else timeSeconds()
    t = tsecs+secs+offset
    return getAsDateTimeStr(t if (tsecs > abs(secs)) else tsecs,fmt=format) if (not use_iso) else datetime.fromtimestamp(t).isoformat()


def find_aws_creds_or_config_src(fpath):
    __root = os.path.dirname(__file__)
    __fpath = fpath.split(os.sep)
    if (__fpath[0] == '.'):
        __fpath = __fpath[1:]
    __fpath = os.sep.join(__fpath)
    while (len(__root.split(os.sep)) > 1):
        __r__ = os.sep.join([__root, __fpath])
        if (os.path.exists(__r__) and os.path.isfile(__r__)):
            return __r__
        __root = os.path.dirname(__root)
    return fpath


def get_something_from_something(l, regex=None, name=None):
    assert regex, 'Missing the regex.'
    matches = re.match(regex, l, re.MULTILINE)
    if (matches):
        if (name):
            return matches.groupdict().get(name).strip()
        else:
            def __func__(k):
                return [ch for ch in k if (ch.isnumeric())]
            return tuple([matches.groupdict().get(k).strip() for k in sorted([k for k in matches.groupdict().keys()], key=__func__)])
    return None

aws_creds = {}
aws_config = {}
def handle_aws_creds_or_config(fpath, dest=None, target=None):
    assert isinstance(target, dict), 'target must be a dict object.'
    __d__ = target
    __s__ = []
    resp = False
    if (os.path.exists(fpath)):
        try:
            if (dest and not os.path.exists(dest)):
                os.mkdir(os.path.dirname(dest))
                Path(dest).touch()
                
            fOut = open(dest, 'w') if (dest is not None) else None
            with open(fpath, 'r') as fIn:
                for l in fIn:
                    l = l.strip()
                    if (len(l) > 0):
                        n = get_something_from_something(l, regex=r"^\[(?P<name>.*)\]$", name='name')
                        if (n):
                            if (len(__s__) > 0):
                                __d__ = __s__.pop()
                            __d__[n] = {}
                            __s__.append(__d__)
                            __d__ = __d__.get(n)
                        else:
                            k,v = get_something_from_something(l, regex=r"^(?P<name1>.*)\=(?P<value2>.*)$")
                            __d__[k] = v
            resp = True
        except:
            resp = False
        finally:
            if (fOut):
                fOut.flush()
                fOut.close()
    return resp


if (__name__ == '__main__'):
    '''
    --clean-ecr ... removes all known repos from the ECR - this is for development purposes only.
    '''
    if (not is_running_production()):
        sys.argv.append(__push_ecr_command_line_option__)
        sys.argv.append(__single_command_line_option__)
        sys.argv.append(__clean_ecr_command_line_option__)
        sys.argv.append(__timetags_command_line_option__)
    
    is_verbose = any([str(arg).find(__verbose_command_line_option__) > -1 for arg in sys.argv])
    if (is_verbose):
        logger.info('verbose: {}'.format(__verbose_command_line_option__))
    
    is_single = any([str(arg).find(__single_command_line_option__) > -1 for arg in sys.argv])
    if (is_single):
        logger.info('{}'.format(__single_command_line_option__))
    
    is_scanOnPush = any([str(arg).find(__scanOnPush_command_line_option__) > -1 for arg in sys.argv])
    if (is_scanOnPush):
        logger.info('{}'.format(__scanOnPush_command_line_option__))
    
    is_cleaning_ecr = any([str(arg).find(__clean_ecr_command_line_option__) > -1 for arg in sys.argv])
    if (is_cleaning_ecr):
        logger.info('{}'.format(__clean_ecr_command_line_option__))
    
    is_pushing_ecr = any([str(arg).find(__push_ecr_command_line_option__) > -1 for arg in sys.argv])
    if (is_pushing_ecr):
        logger.info('{}'.format(__push_ecr_command_line_option__))

    is_timetags = any([str(arg).find(__timetags_command_line_option__) > -1 for arg in sys.argv])
    if (is_timetags):
        logger.info('{}'.format(__timetags_command_line_option__))

    is_dry_run = (not is_cleaning_ecr) and (not is_pushing_ecr)
    if (is_dry_run):
        logger.info('No command line options given. Performing a dry-run with no actions taken.')
    
    __aws_creds_src__ = find_aws_creds_or_config_src(__aws_creds_src__)
    __aws_config_src__ = find_aws_creds_or_config_src(__aws_config_src__)
    
    logger.info('Checking for aws creds.')
    resp = handle_aws_creds_or_config(__aws_creds_src__, target=aws_creds) # , dest=__aws_creds_dest__

    logger.info('Checking for aws config.')
    resp = handle_aws_creds_or_config(__aws_config_src__, target=aws_config) # , dest=__aws_config_dest__

    __aws_access_key_id = aws_creds.get(list(aws_creds.keys())[0], {}).get('aws_access_key_id')
    assert is_really_something(__aws_access_key_id, str), 'Missing the aws_access_key_id, check your config files.'
    
    __aws_secret_access_key = aws_creds.get(list(aws_creds.keys())[0], {}).get('aws_secret_access_key')
    assert is_really_something(__aws_secret_access_key, str), 'Missing the aws_secret_access_key, check your config files.'
    
    ecr_client = boto3.client(
        'ecr',
        aws_access_key_id=__aws_access_key_id,
        aws_secret_access_key=__aws_secret_access_key,
        region_name=aws_config.get(list(aws_config.keys())[0], {}).get('region', 'us-east-2')
    )        

    if (is_pushing_ecr):
        import docker
        docker_client = docker.from_env()
        
        logger.info('{}'.format(' '.join(__docker_containers__)))
        containers = docker_client.containers.list(all=True)
        
        __containers_by_id__ = {}
        for container in containers:
            cname = container.image.tags[0]
            name_to_id[cname] = container.short_id
            id_to_name[container.short_id] = cname
            __containers_by_id__[container.short_id] = container
        
        dead_containers = [name_to_id.get(n)[0] for n in name_to_id.keys() if (n.find(__docker_hello_world__[-1]) > -1)]
        if (len(dead_containers) > 0):
            for _id in dead_containers:
                container = __containers_by_id__.get(_id)
                if (container):
                    container.remove(force=True)

        name_to_id = SmartDict()
        id_to_name = {}

        logger.info('{}'.format(' '.join(__docker_images__)))
        images = docker_client.images.list(all=True)

        __images_by_id__ = {}
        for image in images:
            if (len(image.tags) > 0):
                iname = image.tags[0]
                if (not any([iname.find(i) > -1 for i in __ignoring_images_like_these__])):
                    name_to_id[iname] = image.short_id
                    id_to_name[image.short_id] = iname
                    __images_by_id__[image.short_id] = image

        assert len(id_to_name) > 0, 'There are no docker images to handle.  Please resolve.'
        logger.info('There are {} docker images.'.format(len(id_to_name)))
    
    logger.info('{}'.format(' '.join(__aws_cli_ecr_describe_repos__)))
    response = ecr_client.describe_repositories()
    assert 'repositories' in response.keys(), 'Cannot "{}".  Please resolve.'.format(__aws_cli_ecr_describe_repos__)
    the_repositories = response.get('repositories', [])
    
    if (is_cleaning_ecr): 
        if (len(the_repositories)):
            for repo in the_repositories:
                repo_name = repo.get('repositoryName')
                assert repo_name is not None, 'Cannot remove {} due to the lack of information. Please resolve.'.format(json.dumps(repo, indet=3))
                logger.info('Removing the repo named "{}".'.format(repo_name))
                response = ecr_client.delete_repository(
                    registryId=repo.get('registryId'),
                    repositoryName=repo.get('repositoryName'),
                    force=True
                )                    
                statusKey = [k for k in response.get('ResponseMetadata', {}).keys() if (k.lower().find('statuscode') > -1)][0]
                statusCode = int(eval(str(response.get('ResponseMetadata', {}).get(statusKey, -1))))
                assert statusCode == 200, 'Failed command. The ECR Repo "{}" has not been removed.  Please resolve.'.format(repo.get('repositoryName'))
            logger.info('Finished removing {} repos.'.format(len(the_repositories)))
        else:
            logger.info('Nothing to do.')
    
    if (is_pushing_ecr):
        create_the_repos = []
        for image_id,image_name in id_to_name.items():
            __is__ = False
            possible_repo_name = image_name.split(':')[0]
            if (possible_repo_name not in ignoring_image_names):
                for repo in the_repositories:
                    if (possible_repo_name == repo.get('repositoryName')):
                        __is__ = True
                        continue
                if (not __is__):
                    create_the_repos.append({'name':possible_repo_name.split('/')[-1], 'tag': image_name.split(':')[-1], 'id': image_id})
                    
        #print(json.dumps({'create_the_repos': create_the_repos}, indent=3))
        
        def task(vector={}):
            issues_count = 0
            try:
                _id = vector.get('id')
                assert _id is not None, 'Problem with getting the image id from the docker image. Please fix.'
                name = vector.get('name')
                assert name is not None, 'Problem with getting the image name from the docker image. Please fix.'
                tag = vector.get('tag')
                assert tag is not None, 'Problem with getting the image tag from the docker image. Please fix.'
                
                if (is_timetags):
                    tag = '{}+{}'.format(tag, timeStamp(offset=0, use_iso=True))

                logger.info('Create ECR repo "{}"'.format(name))

                logger.info('{}'.format(' '.join(__aws_cli_ecr_describe_repos__)))
                response = ecr_client.describe_repositories()
                the_repositories = response.get('repositories', [])
                does_repo_exist = False
                for repo in the_repositories:
                    repo_name = repo.get('repositoryName')
                    if (is_really_something(repo_name, str)):
                        if (repo_name == name):
                            does_repo_exist = True
                            repo_uri = repo.get('repositoryUri')
                            break
                
                if (does_repo_exist):
                    logger.info('ECR Repo named "{}" already exists possibly from a previous push so not creating it this time.'.format(name))
                else:
                    cmd = [str(c).replace('{}', name) for c in __aws_cli_ecr_create_repo__]
                    logger.info('Create ECR repo "{}"'.format(' '.join(cmd)))

                    response = ecr_client.create_repository(
                        repositoryName=name,
                        imageScanningConfiguration={
                                'scanOnPush': True if (is_scanOnPush) else False
                            },
                    )                
                
                    repo_uri = response.get('repository', {}).get('repositoryUri')
                    assert repo_uri is not None, 'Cannot tag "{}".  Please resolve.'.format(name)

                cmd = __docker_tag_cmd__.format(_id, repo_uri, tag)
                logger.info('docker tag cmd: "{}"'.format(cmd))

                image = __images_by_id__.get(_id)
                assert image, 'Cannot locate the image for _id ({}).'.format(_id)
                
                if (not is_dry_run):
                    resp = image.tag(repo_uri, tag=tag)
                    assert resp, '{} was not successful.'.format(cmd)
                
                aws_access_token = ecr_client.get_authorization_token()
                username, password = base64.b64decode(aws_access_token['authorizationData'][0]['authorizationToken']).decode().split(':')
                registry = aws_access_token['authorizationData'][0]['proxyEndpoint']
                registry = registry.replace('https://', 'http://')
                
                cmd = __aws_docker_login__.format(repo_uri.split('/')[0])
                logger.info('docker login cmd: "{}"'.format(cmd))

                resp = docker_client.login(username, password, registry=registry)
                assert resp.get('Status') == __expected_aws_docker_login__, 'Cannot login for docker "{}".  Please resolve.'.format(cmd)
                
                cmd = __docker_push_cmd__.format(repo_uri, tag)
                logger.info('docker push cmd: "{}"'.format(cmd))
                
                for resp in docker_client.images.push(repo_uri, tag=tag, stream=True, decode=True):
                    logger.info('{}'.format(resp))
            except Exception:
                logger.error("Fatal error in task", exc_info=True)
                issues_count += 1
            
            vector['result'] = True if (issues_count == 0) else False
            return vector
            
        if (os.path.exists(__docker_config_json__)):
            logger.info('Removing the docker config: "{}" Reason: This file tends to cause issues with the Auto-ECR Process when it exists.'.format(__docker_config_json__))
            os.remove(__docker_config_json__)
        
        if (not is_single):
            __max_workers = len(create_the_repos)+1
            executor = futures.ProcessPoolExecutor(max_workers=__max_workers)

            wait_for = []
            count_started = 0
            for vector in create_the_repos:
                wait_for.append(executor.submit(task, vector))
                count_started += 1
                    
            count_completed = 0
            logger.info('BEGIN: Waiting for tasks to complete.')
            for f in futures.as_completed(wait_for):
                count_completed += 1
                logger.info('main-thread: result: {}'.format(f.result()))
                logger.info('main-thread: Progress: {} of {} or {:.2%} completed'.format(count_completed, count_started, (count_completed / count_started)))
            logger.info('DONE!!! Waiting for tasks to complete.')
        else:
            count_started = len(create_the_repos)
            count_completed = 0
            for vector in create_the_repos:
                result = task(vector=vector)
                count_completed += 1
                logger.info('main-thread: result: {}'.format(result))
                logger.info('main-thread: Progress: {} of {} or {:.2%} completed'.format(count_completed, count_started, (count_completed / count_started)))
            logger.info('DONE!!!')
        
    logger.info('"{}" is DONE!'.format(sys.argv[0]))
