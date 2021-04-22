import os
import re

import boto3

from pathlib import Path

is_really_something = lambda s,t:(s is not None) and (((not callable(t)) and isinstance(s, t)) or ((callable(t) and t(s))))
is_really_something_with_stuff = lambda s,t:is_really_something(s,t) and (len(s) > 0)
something_greater_than_zero = lambda s:(s > 0)
default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]

unpack = lambda l:l[0] if (isinstance(l, list) and (len(l) > 0)) else l

def load_docker_compose(fpath, logger=None):
    import yaml
    
    with open(fpath, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            if (logger):
                logger.error("Fatal error reading docker-compose file.", exc_info=True)
    return None


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


def handle_aws_creds_or_config(fpath, dest=None, target=None):
    assert isinstance(target, dict), 'target must be a dict object.'
    __d__ = target
    __s__ = []
    resp = False
    assert (is_really_something(fpath, str)), 'Missing the fpath. Please ensure there is a value for fpath.'
    assert (isinstance(target, dict)), 'Missing the target. Please ensure there is a value for target which is typically a dict.'
    if (is_really_something(fpath, str)) and (os.path.exists(fpath)):
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


def get_aws_creds_and_config(aws_creds=None, aws_config=None, aws_creds_src=None, aws_config_src=None, logger=None):
    assert (isinstance(aws_creds, dict)), 'Cannot proceed without aws_creds which should be an empty dict.'
    if (isinstance(aws_creds, dict)) and (len(aws_creds) == 0):
        if (logger):
            logger.info('Checking for aws creds.')
        resp = handle_aws_creds_or_config(aws_creds_src, target=aws_creds)
        
    assert (isinstance(aws_config, dict)), 'Cannot proceed without aws_config which should be an empty dict.'
    if (isinstance(aws_config, dict)) and (len(aws_config) == 0):
        if (logger):
            logger.info('Checking for aws config.')
        resp = handle_aws_creds_or_config(aws_config_src, target=aws_config)


def get_ecr_client(aws_creds=None, aws_config=None, aws_creds_src=None, aws_config_src=None, aws_default_region=None, logger=None):
    get_aws_creds_and_config(aws_creds=aws_creds, aws_config=aws_config, aws_creds_src=aws_creds_src, aws_config_src=aws_config_src, logger=logger)

    __aws_access_key_id = aws_creds.get(list(aws_creds.keys())[0], {}).get('aws_access_key_id')
    assert is_really_something(__aws_access_key_id, str), 'Missing the aws_access_key_id, check your config files.'

    __aws_secret_access_key = aws_creds.get(list(aws_creds.keys())[0], {}).get('aws_secret_access_key')
    assert is_really_something(__aws_secret_access_key, str), 'Missing the aws_secret_access_key, check your config files.'

    ecr_client = boto3.client(
        'ecr',
        aws_access_key_id=__aws_access_key_id,
        aws_secret_access_key=__aws_secret_access_key,
        region_name=aws_config.get(list(aws_config.keys())[0], {}).get('region', aws_default_region)
    )
    return ecr_client


def search_ecr_for_image_by_name(image_name, aws_creds=None, aws_config=None, aws_creds_src=None, aws_config_src=None, aws_default_region=None, aws_cli_ecr_describe_repos=None, logger=None):
    ecr_client = get_ecr_client(aws_creds=aws_creds, aws_config=aws_config, aws_creds_src=aws_creds_src, aws_config_src=aws_config_src, aws_default_region=aws_default_region, logger=logger)

    response = ecr_client.describe_repositories()
    assert 'repositories' in response.keys(), 'Cannot "{}".  Please resolve.'.format(aws_cli_ecr_describe_repos)
    the_repositories = response.get('repositories', [])

    if (len(the_repositories)):
        for repo in the_repositories:
            repo_name = repo.get('repositoryName')
            if (image_name.find(repo_name) > -1):
                if (logger):
                    logger.info('image "{}" found in "{}".'.format(image_name, repo_name))
                    return repo.get('repositoryUri')
    return None


def get_environment_for_terraform_from(fpath, logger=None):
    '''
        environment = {
        VAR_1               = "hello"
        VAR_2               = "world"
        }      
    '''
    import os
    import sys

    assert os.path.exists(fpath) and os.path.isfile(fpath), 'Cannot find the terraform environment from "{}".'.format(fpath)

    __env = {}
    
    import __env__
    m = sys.modules.get('__env__')
    assert m is not None, 'Cannot find "__env__". Please resolve.'
    f = getattr(m, 'read_env')
    f(fpath=fpath, environ=__env, is_ignoring=True, override=False, logger=logger)

    if (0):    
        from io import StringIO
        oBuf = StringIO()
        print('environment = {\n', file=oBuf)
        for k,v in __env.items():
            print('{} = "{}"\n'.format(k,v), file=oBuf)
        print('}\n', file=oBuf)
        return oBuf.getvalue()
    
    return __env


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


def get_container_definitions_from(data, source=None, aws_creds=None, aws_config=None, aws_creds_src=None, aws_config_src=None, aws_default_region=None, aws_cli_ecr_describe_repos=None, logger=None):
    '''
        [
            {
            "name": "my-first-task",
            "image": "${aws_ecr_repository.my_first_ecr_repo.repository_url}",
            "essential": true,
            "portMappings": [
                {
                "containerPort": 3000,
                "hostPort": 3000
                }
            ],
            "memory": 512,
            "cpu": 256,
            environment = {
            VAR_1               = "hello"
            VAR_2               = "world"
            }      
        }
        ]
    '''
    container_defs = []
    services = data.get('services', {})
    assert len(services) > 0, 'Missing services so cannot get the container_definitions.'
    for svc_name, svc in services.items():
        container_def = {}
        __name = svc.get('container_name')
        assert is_really_something(__name, str), 'Missing the container_name from a service named "{}".'.format(svc_name)
        __image = svc.get('image')
        assert is_really_something(__image, str), 'Missing the image from a service named "{}".'.format(svc_name)
        __uri = search_ecr_for_image_by_name(__image, aws_creds=aws_creds, aws_config=aws_config, aws_creds_src=aws_creds_src, aws_config_src=aws_config_src, aws_default_region=aws_default_region, aws_cli_ecr_describe_repos=aws_cli_ecr_describe_repos, logger=logger)
        __image = __uri if (is_really_something(__uri, str)) else __image
        __ports = svc.get('ports')
        assert is_really_something(__ports, str), 'Missing the ports from a service named "{}".'.format(svc_name)
        __host_port, __container_port = tuple(unpack(__ports).split(':'))
        __deploy = svc.get('deploy', {})
        __deploy_resources = __deploy.get('resources', {})
        __deploy_resources_limits = __deploy_resources.get('limits', {})
        assert is_really_something_with_stuff(__deploy, dict), 'Missing the deploy from a service named "{}".'.format(svc_name)
        assert is_really_something_with_stuff(__deploy_resources, dict), 'Missing the deploy resources from a service named "{}".'.format(svc_name)
        assert is_really_something_with_stuff(__deploy_resources_limits, dict), 'Missing the deploy resources limits from a service named "{}".'.format(svc_name)
        __cpus = eval(__deploy_resources_limits.get('cpus', '0.0'))
        assert is_really_something(__cpus, float), 'Missing the cpus or its not a numeric value from a service named "{}".'.format(svc_name)
        __memory = __deploy_resources_limits.get('memory')
        assert is_really_something(__memory, str), 'Missing the memory from a service named "{}".'.format(svc_name)
        
        __env = unpack(svc.get('env_file'))
        assert is_really_something(source, str) and os.path.isdir(source), 'Missing the source directory.'
        if (is_really_something(__env, str)):
            __env = os.sep.join([source, __env])
            assert is_really_something(__env, str) and os.path.isfile(__env), 'Missing the __env file ("{}").'.format(__env)
            container_def['environment'] = get_environment_for_terraform_from(__env)

        container_def['name'] = __name
        container_def['image'] = __image
        container_def['essential'] = True
        portMappings = []
        portMapping = {}
        portMapping['containerPort'] = __container_port
        portMapping['hostPort'] = __host_port
        portMappings.append(portMapping)
        container_def['portMappings'] = portMappings
        container_def['memory'] = __memory
        container_def['cpu'] = __cpus
        container_defs.append(container_def)
    return container_defs

