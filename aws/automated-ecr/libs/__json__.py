import os
import sys
import json
import traceback

import re

from logging import exception
from typing import Union

try:
    from .__utils__ import unpack
    from .__utils__ import save_json_data
    from .__utils__ import default_timestamp
    from .__utils__ import load_docker_compose
    from .__utils__ import is_really_something
    from .__utils__ import something_greater_than_zero
    from .__utils__ import find_aws_creds_or_config_src
    from .__utils__ import is_really_something_with_stuff
    from .__utils__ import get_container_definitions_from
    from .__utils__ import get_environment_for_terraform_from
except ImportError:
    def import_func_from(func_name, module):
        func = getattr(module, func_name)
        assert callable(func), 'Cannot find {} in {}.'.format(func_name, module.__name__)
        return func

    func_names = ['unpack', 'save_json_data', 'default_timestamp', 'load_docker_compose', 'is_really_something', 'something_greater_than_zero', 'find_aws_creds_or_config_src', 'is_really_something_with_stuff', 'get_container_definitions_from', 'get_environment_for_terraform_from']

    __self__ = sys.modules.get(__name__)

    __utils__ = None
    modules = [m for m in sys.modules if (m.find('__utils__') > -1)]
    if (len(modules) > 0):
        __utils__ = sys.modules.get(modules[0])
        for n in func_names:
            f = import_func_from(n, __utils__)
            setattr(__self__, n, f)


def handle_normalization(**kwargs):
    ch = kwargs.get('ch')
    toks = kwargs.get('toks', [])
    replacements = kwargs.get('replacements', {})
    if (ch):
        toks[0] = toks[0].replace('"', '')
    if (len(toks) > 2):
        toks[1] = ch.join(toks[1:])
        del toks[2:]
    return replacements.get(ch).join(toks)


def snip_surrounding_chars(s, chars="{}"):
    ch1 = chars[0]
    for i in range(0, len(s)):
        if (s[i] == ch1):
            i += 1
            break
    ch2 = chars[-1]
    for j in range(len(s)-1, 0, -1):
        if (s[j] == ch2):
            j -= 1
            break
    return s[i:j]


class CompactJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small containers on single lines."""

    CONTAINER_TYPES = (list, tuple, dict)
    """Container datatypes include primitives or other containers."""

    MAX_WIDTH = 70
    """Maximum width of a container that might be put on a single line."""

    MAX_ITEMS = 2
    """Maximum number of items in container that might be put on single line."""

    INDENTATION_CHAR = " "

    def __init__(self, *args, **kwargs):
        self._replacements = kwargs.get('__replacements')
        if ('__replacements' in list(kwargs.keys())):
            del kwargs['__replacements']
        self._callback = kwargs.get('__callback')
        if ('__callback' in list(kwargs.keys())):
            del kwargs['__callback']
        self._use_commas = kwargs.get('__use_commas')
        if ('__use_commas' in list(kwargs.keys())):
            del kwargs['__use_commas']
        self._use_commas_exceptions = kwargs.get('__use_commas_exceptions')
        if ('__use_commas_exceptions' in list(kwargs.keys())):
            del kwargs['__use_commas_exceptions']
        self._use_equals_exceptions = kwargs.get('_use_equals_exceptions')
        if ('_use_equals_exceptions' in list(kwargs.keys())):
            del kwargs['_use_equals_exceptions']
        super().__init__(*args, **kwargs)
        self.indent if (self.indent) else 0
        self.indentation_level = 0

    def encode(self, o, use_commas=False):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            if self._put_on_single_line(o):
                return "[" + ", ".join(self.encode(el) for el in o) + "]"
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el, use_commas=use_commas) for el in o]
                self.indentation_level -= 1
                return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(o, dict):
            def normalize(value):
                __splits = list(self._replacements.keys())
                for s in __splits:
                    __toks = value.split(s)
                    if (len(__toks) > 1):
                        if (callable(self._callback)):
                            try:
                                value = self._callback(ch=s, toks=__toks, replacements={s : self._replacements.get(s)})
                            except Exception as ex:
                                print(ex)
                return value
            
            def normalize_commas(value, use_commas=self._use_commas):
                return value.replace(',', '') if (not use_commas) else value
            if o:
                if self._put_on_single_line(o):
                    return "{ " + normalize_commas(", ", use_commas=use_commas).join(normalize(f"{self.encode(k)}: {self.encode(el)}") for k, el in o.items()) + " }"
                else:
                    self.indentation_level += 1
                    f = self._use_commas_exceptions
                    if (f is None):
                        f = {}
                    f_use_commas = self._use_commas
                    output = [self.indent_str + normalize(f"{json.dumps(k)}: {self.encode(v, use_commas=f.get(k, f_use_commas))}") for k, v in o.items()]
                    self.indentation_level -= 1
                    if (isinstance(self._use_equals_exceptions, dict)):
                        _replacements = []
                        for i, __o__ in enumerate(output):
                            for k,v in self._use_equals_exceptions.items():
                                if (__o__.find(k) > -1) and (not v):
                                    _regex = r"{}\s*\=".format(k)
                                    _subst = "{}".format(k)
                                    _result = re.sub(_regex, _subst, __o__, 0, re.MULTILINE)
                                    if (_result):
                                        _replacements.append(tuple([i, _result]))
                                        break
                        if (len(_replacements) > 0):
                            for i,s in _replacements:
                                output[i] = s
                    return "{\n" + normalize_commas(",\n").join(output) + "\n" + self.indent_str + "}"
            else:
                return "{}"
        elif isinstance(o, float):  # Use scientific notation for floats, where appropiate
            return format(o, "g")
        elif isinstance(o, str):  # escape newlines
            o = o.replace("\n", "\\n")
            return f'"{o}"'
        else:
            return json.dumps(o)

    def _put_on_single_line(self, o):
        return self._primitives_only(o) and len(o) <= self.MAX_ITEMS and len(str(o)) - 2 <= self.MAX_WIDTH

    def _primitives_only(self, o: Union[list, tuple, dict]):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self) -> str:
        return self.INDENTATION_CHAR*(self.indentation_level*self.indent)


class TerraformSectionFactory(object):
    def section_named(self, name, callback=None, **kwargs):
        from collections import namedtuple
        Section = namedtuple('Section', ['name', 'callback', 'kwargs'])
        return Section(name=name, callback=callback, kwargs=kwargs)


def render_terraform_vars(env):
    '''
    default = [
    {
    "name" = "BUCKET",
    "value" = "test"
    },{
    "name" = "BUCKET1",
    "value" = "test1"
    }]
    '''
    vars = []
    for k,v in env.items() if (isinstance(env, dict)) else env:
        vars.append({'name': k, 'value': v})
    return vars


class TerraformFile(TerraformSectionFactory, dict):
    '''
    dict of named tuples handles output.
    '''
    def __renderProvider(**kwargs):
        provider = kwargs.get('provider')
        if (is_really_something(provider, str)):
            del kwargs['provider']
        data = {}
        for k,v in kwargs.items():
            data[k] = v
        _json = json.dumps(data, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __callback=handle_normalization)
        results = '''provider "{}" {}
            {}
{}
'''.format(provider, '{', snip_surrounding_chars(_json), '}')
        return results


    def __renderResource(**kwargs):
        resource = kwargs.get('resource')
        if (is_really_something(resource, str)):
            del kwargs['resource']
        name2 = kwargs.get('name2')
        if (is_really_something(name2, str)):
            del kwargs['name2']
            kwargs['name'] = name2
        _ignores = kwargs.get('kwargs', {}).get('ignores', [])
        if ('ignores' in list(kwargs.keys())):
            del kwargs['kwargs']
        _ignores = _ignores if (isinstance(_ignores, list)) else []
        _ignores = list(set(_ignores).union(set(['kwargs'])))
        data = {}
        for k,v in kwargs.items():
            if (k not in _ignores):
                data[k] = v
        container_definitions = None
        s_container_definitions = ''
        _container_definitions = []
        _use_commas_exceptions = None
        if ('container_definitions' in list(data.keys())):
            container_definitions = data.get('container_definitions')
            if (container_definitions):
                has_many_container_definitions = len(container_definitions) > 1
                s_container_definitions = '\ncontainer_definitions = <<DEFINITION\n'
                for cdef in container_definitions:
                    container_definition_env = cdef.get('environment')
                    if (container_definition_env):
                        cdef['environment'] = render_terraform_vars(container_definition_env)
                    container_definition_ports = cdef.get('portMappings')
                    if (container_definition_ports):
                        cdef['portMappings'] = render_terraform_vars(container_definition_ports)
                    container_definition_memory = cdef.get('memory')
                    if (container_definition_memory):
                        cdef['memory'] = eval(''.join([ch for ch in container_definition_memory if (str(ch).isdigit())]))
                    _container_definitions.append(cdef)
                s_json = json.dumps(_container_definitions, cls=CompactJSONEncoder, indent=3, __replacements={}, __use_commas=True)
                s_container_definitions = s_container_definitions + s_json + '\n'
                s_container_definitions = s_container_definitions + "DEFINITION" + '\n'
                del data['container_definitions']
            _use_commas_exceptions = {'portMappings': True}
        _use_equals_exceptions = None
        if ('network_configuration' in list(data.keys())):
            _use_equals_exceptions = {'network_configuration': False}
        _json = json.dumps(data, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __use_commas_exceptions=_use_commas_exceptions, _use_equals_exceptions=_use_equals_exceptions, __callback=handle_normalization)
        results = '''resource "{}" {} {}
            {}{}
{}
'''.format(resource, name2, '{', snip_surrounding_chars(_json), s_container_definitions, '}')
        return results


    def __renderData(**kwargs):
        return TerraformFile.__renderResource(**kwargs)


    def __renderInit(**kwargs):
        results = ''
        required_providers = kwargs.get('required_providers')
        if (is_really_something(required_providers, str)):
            results ='''terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "3.38.0"
        }
    }
}
'''
        return results


    def addInit(self, terraform='init', required_providers='aws', callback=None):
        '''
            terraform {
                required_providers {
                    aws = {
                        source = "hashicorp/aws"
                        version = "3.38.0"
                    }
                }
            }
        '''
        if (not callable(callback)):
            callback = TerraformFile.__renderInit
        self['terraform'] = self.section_named('required_providers', callback=callback, required_providers=required_providers)
        return self['terraform']


    def addProvider(self, provider='aws', region='us-east-2', callback=None):
        '''
            provider "aws" {
                region  = "eu-west-2" # this comes from the aws config files.
            }
        '''
        if (not callable(callback)):
            callback = TerraformFile.__renderProvider
        self['provider'] = self.section_named('provider', callback=callback, provider=provider, region=region)
        return self['provider']


    def addResource(self, resource='aws_ecr_repository', name='my_first_ecr_repo', callback=None, ignores=None):
        '''
            resource "aws_ecr_repository" "my_first_ecr_repo" {
                name = "my-first-ecr-repo" # Naming my repository
            }            
        '''
        if (not callable(callback)):
            callback = TerraformFile.__renderResource
        self[resource] = self.section_named('resource', callback=callback, resource=resource, name2=name, kwargs={'ignores':ignores})
        return self[resource]


    def addData(self, resource='aws_iam_policy_document', name='assume_role_policy', callback=None):
        '''
            data "aws_iam_policy_document" "assume_role_policy" {
            statement {
                actions = ["sts:AssumeRole"]

                principals {
                type        = "Service"
                identifiers = ["ecs-tasks.amazonaws.com"]
                }
            }
            }
        '''
        if (not callable(callback)):
            callback = TerraformFile.__renderData
        self[resource] = self.section_named('data', callback=callback, resource=resource, name2=name)
        return self[resource]


    def saveResource(self, resource=None):
        self[resource.kwargs.get('resource')] = resource


    @property
    def content(self):
        results = []
        for _,section in self.items():
            if (callable(section.callback)):
                try:
                    resp = section.callback(**section.kwargs)
                    results.append(resp)
                except Exception as ex:
                    extype, ex, tb = sys.exc_info()
                    print('EXCEPTION:')
                    for l in traceback.format_exception(extype, ex, tb):
                        print(l.rstrip())
                    print('-'*30)
                    print()
        return ''.join(results)


def get_terraform_init_file_contents(logger=None):
    tf = TerraformFile()
    tf.addInit()
    return tf.content


def get_terraform_file_contents(docker_compose_data, do_init=False, aws_ecs_cluster_name=None, aws_ecs_repo_name=None, docker_compose_location=None, aws_creds=None, aws_config=None, aws_creds_src=None, aws_config_src=None, aws_default_region=None, aws_cli_ecr_describe_repos=None, aws_ecs_compute_engine=None):
    tf = TerraformFile()
    if (do_init):
        tf.addInit()

    _default_zone = aws_config.get('default', {}).get('region', 'us-east-2')
    tf.addProvider(provider='aws', region=_default_zone)
    tf.addResource(resource='aws_ecr_repository', name=aws_ecs_repo_name)
    tf.addResource(resource='aws_ecs_cluster', name=aws_ecs_cluster_name)
    
    resource = tf.addResource(resource='aws_ecs_task_definition', name='my_first_task', ignores=['name'])
    resource.kwargs['family'] = 'my-first-task'
    
    container_definitions = get_container_definitions_from(docker_compose_data, source=os.path.dirname(docker_compose_location), aws_creds=aws_creds, aws_config=aws_config, aws_creds_src=aws_creds_src, aws_config_src=aws_config_src, aws_default_region=aws_default_region, aws_cli_ecr_describe_repos=aws_cli_ecr_describe_repos)

    resource.kwargs['container_definitions'] = container_definitions
    resource.kwargs['requires_compatibilities'] = ["FARGATE"]
    resource.kwargs['network_mode'] = "awsvpc"
    #resource.kwargs['execution_role_arn'] = "aws_iam_role.ecsTaskExecutionRole.arn"
    tf.saveResource(resource=resource)

    if (0):
        resource = tf.addResource(resource='aws_iam_role', name='ecsTaskExecutionRole')
        resource.kwargs['assume_role_policy'] = "data.aws_iam_policy_document.assume_role_policy.json"
        tf.saveResource(resource=resource)

    if (0):
        resource = tf.addData(resource='aws_iam_policy_document', name='assume_role_policy')
        resource.kwargs['statement'] = {}
        resource.kwargs['statement']['actions'] = ["sts:AssumeRole"]
        resource.kwargs['statement']['principals'] = {}
        resource.kwargs['statement']['principals']['type'] = "Service"
        resource.kwargs['statement']['principals']['identifiers'] = ["ecs-tasks.amazonaws.com"]
        tf.saveResource(resource=resource)

    resource = tf.addData(resource='aws_ecs_service', name='my_first_service')
    resource.kwargs['name'] = "my-first-service"
    resource.kwargs['cluster'] = "aws_ecs_cluster.my_cluster.id"
    resource.kwargs['task_definition'] = "aws_ecs_task_definition.my_first_task.arn"
    resource.kwargs['launch_type'] = aws_ecs_compute_engine
    resource.kwargs['desired_count'] = 1
    resource.kwargs['network_configuration'] = {
        'subnets': ["aws_default_subnet.default_subnet_a.id"],
        'assign_public_ip' : True
    }
    tf.saveResource(resource=resource)


    def handle_aws_default_vpc(**kwargs):
        '''
        resource "aws_default_vpc" "default_vpc" {
        }
        '''
        resource = kwargs.get('resource')
        if (resource):
            del kwargs['resource']
        name2 = kwargs.get('name2')
        if (name2):
            del kwargs['name2']
        _kwargs = kwargs.get('kwargs')
        if (_kwargs):
            del kwargs['kwargs']
        resp = 'resource "{}" "{}"'.format(resource, name2)
        _json = json.dumps(kwargs, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __callback=handle_quotes_normalization)
        __is__ = False
        for i,ch in enumerate(_json):
            if (ch == '{'):
                __is__ = True
                break
        if (__is__) and (ch == '{'):
            _json = _json[0:i+1] + '\n' + _json[i+1:]
        resp += _json + '\n'
        return resp


    resource = tf.addResource(resource='aws_default_vpc', name='default_vpc', callback=handle_aws_default_vpc)
    tf.saveResource(resource=resource)


    #import itertools
    def enumerateReversed(l):
        return zip(reversed(range(len(l))), reversed(l))


    def handle_quotes_normalization(**kwargs):
        ch = kwargs.get('ch')
        toks = kwargs.get('toks', [])
        replacements = kwargs.get('replacements', {})
        for k,v in replacements.items():
            ch = ch.replace(k, v)
        toks[0] = toks[0].replace('"', '')
        return ch.join(toks)


    def handle_aws_default_subnet(**kwargs):
        '''
        resource "aws_default_subnet" "default_subnet_a" {
            availability_zone = "eu-west-2a"
        }
        '''
        resource = kwargs.get('resource')
        if (resource):
            del kwargs['resource']
        name2 = kwargs.get('name2')
        if (name2):
            del kwargs['name2']
        _kwargs = kwargs.get('kwargs')
        if (_kwargs):
            del kwargs['kwargs']
        resp = 'resource "{}" "{}"'.format(resource, name2)
        _json = json.dumps(kwargs, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __callback=handle_quotes_normalization)
        __is__ = False
        for i,ch in enumerate(_json):
            if (ch == '{'):
                __is__ = True
                break
        if (__is__) and (ch == '{'):
            _json = _json[0:i+1] + '\n' + _json[i+1:]
        __is__ = False
        for i,ch in enumerateReversed(_json):
            if (ch == '}'):
                __is__ = True
                break
        if (__is__) and (ch == '}'):
            _json = _json[0:i] + '\n' + _json[i:]
        resp += _json
        return resp # TerraformFile.__renderResource(**kwargs)
    
    resource = tf.addResource(resource='aws_default_subnet', name='default_subnet_a', callback=handle_aws_default_subnet)
    resource.kwargs['availability_zone'] = _default_zone
    tf.saveResource(resource=resource)

    return tf.content

    
if (__name__ == '__main__'):
    aws_creds = {}
    aws_config = {}

    __aws_default_region__ = 'us-east-2'
    __aws_cli_ecr_describe_repos__ = ['aws', 'ecr', 'describe-repositories']

    __aws_creds_src__ = './.aws/credentials'
    __aws_config_src__ = './.aws/config'

    __aws_creds_src__ = find_aws_creds_or_config_src(__aws_creds_src__)
    __aws_config_src__ = find_aws_creds_or_config_src(__aws_config_src__)

    __docker_root = '/home/raychorn/projects/python-projects/sample-docker-data'
    __docker_compose_filename__ = 'docker-compose.yml'
    __docker_compose_location = os.sep.join([__docker_root, __docker_compose_filename__])

    docker_compose_data = load_docker_compose(__docker_compose_location)

    __content = get_terraform_file_contents(docker_compose_data, aws_ecs_cluster_name='my_cluster', docker_compose_location=__docker_compose_location, aws_creds=aws_creds, aws_config=aws_config, aws_creds_src=__aws_creds_src__, aws_config_src=__aws_config_src__, aws_default_region=__aws_default_region__, aws_cli_ecr_describe_repos=__aws_cli_ecr_describe_repos__)
    print(__content)
    save_json_data(__docker_compose_location.replace('docker-compose.yml', 'terraform-compose.tf'), __content)
    print('DONE!')