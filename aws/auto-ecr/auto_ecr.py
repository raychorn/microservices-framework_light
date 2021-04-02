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

import mujson as json

__aws_creds_dest__ = os.path.expanduser('~/.aws/credentials')
__aws_creds_src__ = './.aws/credentials'

__aws_config_dest__ = os.path.expanduser('~/.aws/config')
__aws_config_src__ = './.aws/config'

__cat_aws_creds__ = ['cat', __aws_creds_dest__]
__cat_aws_config__ = ['cat', __aws_config_dest__]

__aws_version__ = ['aws', '--version']
__docker_images__ = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}={{.ID}}']

__docker_containers__ = ['docker', 'ps', '-a', '--format', '{{.Image}}={{.ID}}']

__aws_cli_installer__ = ['./scripts/aws-cli-installer.sh']

__resolve_docker_issues__ = ['./scripts/resolve-docker-issues.sh']

__docker_hello_world__ = ['docker', 'run', 'hello-world']

__aws_cli_login__ = ['aws ecr get-login --no-include-email --region us-east-2']
__aws_cli_login__ = __aws_cli_login__[0].split()

__aws_cli_ecr_describe_repos__ = ['aws', 'ecr', 'describe-repositories']

__aws_cli_ecr_create_repo__ = ['aws', 'ecr', 'create-repository', '--repository-name', '{}', '--image-scanning-configuration', 'scanOnPush=true']

__aws_cmd_ecr_delete_repo__ = 'aws ecr delete-repository --repository-name {} --force'

__docker_tag_cmd__ = 'docker tag {} {}:{}'

__docker_push_cmd__ = 'docker push {}:{}'

__docker_remove_container_by_id__ = 'docker container rm {}'

__aws_docker_login__cmd__ = 'aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin {}'

__docker_system_prune__ = ['yes | docker system prune -a']

__aws_cli__ = 'aws-cli/2.'
__hello_from_docker__ = 'Hello from Docker!'
__no_such_file_or_directory__ = 'No such file or directory'

__docker_pulls__ = './script/pulls.sh'

__aws_docker_login__ = './scripts/aws-docker-login.sh {}'
__expected_aws_docker_login__ = 'Login Succeeded'

production_token = 'production'
development_token = 'development'

is_really_something = lambda s,t:s and t(s)
something_greater_than_zero = lambda s:(s > 0)
default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]
is_running_production = lambda : (socket.gethostname() != 'DESKTOP-8H4F8R5')

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

def handle_resolve_docker_issues(item):
    logger.info('DEBUG:  handle_resolve_docker_issues --> {}'.format(item))
    return True


def handle_docker_hello(item):
    try:
        __is__ = item.find(__hello_from_docker__)
        if (__is__ == -1):
            return False
        assert (__is__ > -1), 'Missing {}'.format(__hello_from_docker__)
        logger.info('{}'.format(item))
    except:
        return False
    return True


def handle_aws_cli_installer(item):
    logger.info('DEBUG:  handle_aws_cli_installer --> {}'.format(item))
    return True


def install_aws_cli():
    logger.info('Installing aws cli.')
    result = subprocess.run(__aws_cli_installer__, stdout=subprocess.PIPE)
    handle_stdin(result.stdout, callback2=handle_aws_cli_installer, verbose=True)


def resolve_docker_issues():
    logger.info('Resolving docker issues.')
    result = subprocess.run(__resolve_docker_issues__, stdout=subprocess.PIPE)
    handle_stdin(result.stdout, callback2=handle_resolve_docker_issues, verbose=True)



def handle_aws_docker_login(item):
    logger.info('DEBUG:  handle_aws_docker_login --> {}'.format(item))
    return True


def handle_aws_version(item):
    __vector__ = response_vectors.get(__aws_cli__, None)
    if (__vector__ is None):
        try:
            __is__ = item.find(__aws_cli__)
            if (__is__ == -1):
                return False
            assert (__is__ > -1), 'Missing {}'.format(__aws_cli__)
            logger.info('{}'.format(item))
            response_vectors[__aws_cli__] = __is__
        except:
            return False
    return True

def resolve_missing_file_dest(src_name, dest_name):
    if (dest_name.find('~') > -1):
        dest_name = os.path.expanduser(dest_name)
    if (src_name.find('~') > -1):
        src_name = os.path.expanduser(src_name)
    if (not os.path.exists(dest_name)):
        assert os.path.exists(src_name) and os.path.isfile(src_name), 'Missing {}. Please resolve.'.format(src_name)
        Path(dest_name).touch()
        shutil.copyfile(src_name, dest_name)
        assert os.path.exists(dest_name) and os.path.isfile(dest_name), 'Missing {}. Please resolve by ensuring {} is available.'.format(dest_name, src_name)

def handle_cat_aws_creds(item):
    resolve_missing_file_dest(__aws_creds_src__, __aws_creds_dest__)
    return os.path.exists(os.path.expanduser(__aws_creds_dest__)) and os.path.isfile(os.path.expanduser(__aws_creds_dest__))

def handle_cat_aws_config(item):
    resolve_missing_file_dest(__aws_config_src__, __aws_config_dest__)
    return os.path.exists(os.path.expanduser(__aws_config_dest__)) and os.path.isfile(os.path.expanduser(__aws_config_dest__))



def handle_aws_login(item):
    return None


def handle_ecr_describe_repos(item):
    return None


def parse_docker_image_ls(line):
    return line.replace("b'", "").split('=')


def parse_docker_ps(line):
    return line.replace("b'", "").split('=')


def handle_docker_item(item):
    if (all([len(t.strip()) > 1 for t in item])):
        name_to_id[item[0]] = item[-1]
        id_to_name[item[-1]] = item[0]


def handle_docker_ps_item(item):
    if (all([len(t.strip()) > 1 for t in item])):
        name_to_id[item[0]] = item[-1]
        id_to_name[item[-1]] = item[0]


def json_loads(content):
    content = content.replace("b\'", "").replace("\'", "")
    return json.loads(content)


def handle_stdin(stdin, callback=None, verbose=False, callback2=None, is_json=False):
    response_content = []
    lines = str(stdin).split('\\n')
    for line in lines:
        resp = None
        if (verbose):
            print(line)
        if (callable(callback)):
            try:
                __item__ = callback(line)
            except Exception as ex:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                del exc_info
        item = line if (not callable(callback)) else __item__
        if (callable(callback2)):
            try:
                resp = callback2(item)
                if (resp):
                    break
            except Exception as ex:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                del exc_info
        response_content.append(item)
    __content = ''.join(response_content) if (not isinstance(response_content[0] if (len(response_content) > 0) else response_content, list)) else ''
    if (len(__content) > 0):
        regex = r"^b\'(?P<content>.*)\'$"
        matches = re.search(regex, __content)
        __content = matches.groupdict().get('content') if (matches) else __content
    if (is_json):
        data = json_loads(__content) if (len(__content) > 0) else {}
    if (verbose):
        logger.info('DEBUG: __content -> {}'.format(__content))
        logger.info('DEBUG: resp -> {}'.format(resp is not None))
    return resp if (resp is not None) else data if (is_json) else __content

__clean_ecr_command_line_option__ = '--clean-ecr'
__push_ecr_command_line_option__ = '--push-ecr'

if (__name__ == '__main__'):
    '''
    --clean-ecr ... removes all known repos from the ECR - this is for development purposes only.
    '''
    is_cleaning_ecr = any([str(arg).find(__clean_ecr_command_line_option__) > -1 for arg in sys.argv])
    if (is_cleaning_ecr):
        logger.info('{}'.format(__clean_ecr_command_line_option__))
    
    is_pushing_ecr = any([str(arg).find(__push_ecr_command_line_option__) > -1 for arg in sys.argv])
    if (is_pushing_ecr):
        logger.info('{}'.format(__push_ecr_command_line_option__))
    
    logger.info('Checking for aws creds.')
    result = subprocess.run(__cat_aws_creds__, stdout=subprocess.PIPE)
    resp = handle_stdin(result.stdout, callback2=handle_cat_aws_creds, verbose=True)
    if (resp != True):
        os.mkdir(os.path.dirname(__aws_creds_dest__))
        Path(__aws_creds_dest__).touch()

    logger.info('Checking for aws config.')
    result = subprocess.run(__cat_aws_config__, stdout=subprocess.PIPE)
    resp = handle_stdin(result.stdout, callback2=handle_cat_aws_config, verbose=True)
    if (resp != True):
        os.mkdir(os.path.dirname(__aws_config_dest__))
        Path(__aws_config_dest__).touch()

    if (0):
        logger.info('Using the aws creds.')
        result = subprocess.run(__aws_cli_login__, stdout=subprocess.PIPE)
        resp = handle_stdin(result.stdout, callback2=handle_aws_login, verbose=False)
        assert resp == True, 'Cannot login using the aws creds.  Please resolve.'

    logger.info('Checking for aws cli version 2.')
    resp = None
    while (1):
        try:
            result = subprocess.run(__aws_version__, stdout=subprocess.PIPE)
            resp = handle_stdin(result.stdout, callback2=handle_aws_version, verbose=False)
            break
        except Exception as ex:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
            
            install_aws_cli()
        finally:
            if (not resp):
                logger.info('Warning: Cannot resolve aws cli issues automatically. Please run the script manually. See the "script" directory.')
                break

    if (not is_cleaning_ecr):
        resp = None
        while (1):
            try:
                logger.info('Checking for docker.')
                result = subprocess.run(__docker_hello_world__, stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback2=handle_docker_hello, verbose=False)
                break
            except Exception as ex:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                del exc_info
                
                resolve_docker_issues()
            finally:
                if (not resp):
                    logger.info('Warning: Cannot resolve docker issues automatically. Please run the script manually. See the "script" directory.')
                    break

        result = subprocess.run(__docker_containers__, stdout=subprocess.PIPE)
        resp = handle_stdin(result.stdout, callback=parse_docker_ps, callback2=handle_docker_ps_item, verbose=False)
        
        dead_containers = name_to_id.get(__docker_hello_world__[-1], [])
        if (len(dead_containers) > 0):
            for _id in dead_containers:
                result = subprocess.run(__docker_remove_container_by_id__.format(_id).split(), stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback=None, callback2=None, verbose=False)
                assert resp == _id, 'Something went wrong when trying to remove container #{}.'.format(_id)
                logger.info(resp)

        name_to_id = SmartDict()
        id_to_name = {}

        result = subprocess.run(__docker_images__, stdout=subprocess.PIPE)
        resp = handle_stdin(result.stdout, callback=parse_docker_image_ls, callback2=handle_docker_item, verbose=False)
        if (0):
            logger.info(len(id_to_name))
            with open(__docker_pulls__, 'w') as fOut:
                logger.info('#!/usr/bin/env bash\n', file=fOut)
                for k,v in id_to_name.items():
                    logger.info('{} -> {}'.format(k,v))
                    logger.info('docker pull {}'.format(v), file=fOut)
                    
        assert len(id_to_name) > 0, 'There are no docker images to handle.  Please resolve.'
        logger.info('There are {} docker images.'.format(len(id_to_name)))
    
    logger.info('{}'.format(__aws_cli_ecr_describe_repos__))
    result = subprocess.run(__aws_cli_ecr_describe_repos__, stdout=subprocess.PIPE)
    resp = handle_stdin(result.stdout, callback2=None, verbose=False, is_json=True)
    assert 'repositories' in resp.keys(), 'Cannot "{}".  Please resolve.'.format(__aws_cli_ecr_describe_repos__)
    the_repositories = resp.get('repositories', [])
    
    if (is_cleaning_ecr): # this is only for development.
        if (len(the_repositories)):
            for repo in the_repositories:
                repo_name = repo.get('repositoryName')
                assert repo_name is not None, 'Cannot remove {} due to the lack of information. Please resolve.'.format(json.dumps(repo, indet=3))
                logger.info('Removing the repo named "{}".'.format(repo_name))
                cmd = __aws_cmd_ecr_delete_repo__.format(repo_name)
                result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback2=None, verbose=False, is_json=True)
                assert 'repository' in resp.keys(), 'Cannot "{}".  Please resolve.'.format(cmd)
            logger.info('Done.')
        else:
            logger.info('Nothing to do.')
    
    if (not is_cleaning_ecr):
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
                    
        print(json.dumps({'create_the_repos': create_the_repos}, indent=3))
        
        def task(vector={}):
            issues_count = 0
            try:
                _id = vector.get('id')
                assert _id is not None, 'Problem with getting the image id from the docker image. Please fix.'
                name = vector.get('name')
                assert name is not None, 'Problem with getting the image name from the docker image. Please fix.'
                tag = vector.get('tag')
                assert tag is not None, 'Problem with getting the image tag from the docker image. Please fix.'

                logger.info('Create ECR repo "{}"'.format(name))
                cmd = [str(c).replace('{}', name) for c in __aws_cli_ecr_create_repo__]
                result = subprocess.run(cmd, stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback2=None, verbose=False, is_json=True)
                #assert 'repository' in resp.keys(), 'Cannot "{}".  Please resolve.'.format(' '.join(cmd))

                repo_uri = resp.get('repository', {}).get('repositoryUri')
                assert repo_uri is not None, 'Cannot tag "{}".  Please resolve.'.format(name)

                cmd = __docker_tag_cmd__.format(_id, repo_uri, tag)
                result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback2=None, verbose=False, is_json=False)

                cmd = __aws_docker_login__.format(repo_uri.split('/')[0])
                result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback2=None, verbose=True, is_json=False)
                assert resp == __expected_aws_docker_login__, 'Cannot login for docker "{}".  Please resolve.'.format(cmd)
                
                cmd = __docker_push_cmd__.format(repo_uri, tag)
                logger.info('BEGIN: {}'.format(cmd))
                logger.info('\t\tPlease be patient this will take some time.')
                result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
                resp = handle_stdin(result.stdout, callback2=None, verbose=False, is_json=False)
                assert repo_uri is not None, 'Cannot tag "{}".  Please resolve.'.format(name)
                logger.info('END: {}'.format(cmd))
                logger.info('\n')
            except:
                issues_count += 1
            
            vector['result'] = True if (issues_count == 0) else False
            return vector
            
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
    
    if (0):
        logger.info('{}'.format(__docker_system_prune__))
        result = subprocess.run(__docker_system_prune__, stdout=subprocess.PIPE)
        resp = handle_stdin(result.stdout, callback2=None, verbose=False, is_json=False)
    
        