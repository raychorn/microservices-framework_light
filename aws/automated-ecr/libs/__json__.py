import sys
import json
import traceback

from logging import exception
from typing import Union

from __utils__ import default_timestamp
from __utils__ import is_really_something
from __utils__ import something_greater_than_zero
from __utils__ import is_really_something_with_stuff


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
        self.__replacements = kwargs.get('__replacements')
        if ('__replacements' in list(kwargs.keys())):
            del kwargs['__replacements']
        self.__callback = kwargs.get('__callback')
        if ('__callback' in list(kwargs.keys())):
            del kwargs['__callback']
        self.__use_commas = kwargs.get('__use_commas')
        if ('__use_commas' in list(kwargs.keys())):
            del kwargs['__use_commas']
        super().__init__(*args, **kwargs)
        self.indent if (self.indent) else 0
        self.indentation_level = 0

    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            if self._put_on_single_line(o):
                return "[" + ", ".join(self.encode(el) for el in o) + "]"
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el) for el in o]
                self.indentation_level -= 1
                return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(o, dict):
            def normalize(value):
                __splits = list(self.__replacements.keys())
                for s in __splits:
                    __toks = value.split(s)
                    if (len(__toks) > 1):
                        if (callable(self.__callback)):
                            try:
                                value = self.__callback(ch=s, toks=__toks, replacements={s : self.__replacements.get(s)}) # {'ch': s, 'toks': __toks, 'replacements': {s : self.__replacements.get(s)}}
                            except Exception as ex:
                                print(ex)
                return value
            
            def normalize_commas(value):
                return value.replace(',', '') if (not self.__use_commas) else value
            if o:
                if self._put_on_single_line(o):
                    return "{ " + normalize_commas(", ").join(normalize(f"{self.encode(k)}: {self.encode(el)}") for k, el in o.items()) + " }"
                else:
                    self.indentation_level += 1
                    output = [self.indent_str + normalize(f"{json.dumps(k)}: {self.encode(v)}") for k, v in o.items()]
                    self.indentation_level -= 1
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


class TerraformFile(TerraformSectionFactory, dict):
    '''
    dict of named tuples handles output.
    '''
    def __renderProvider(**kwargs):
        __provider = kwargs.get('provider')
        if (is_really_something(__provider, str)):
            del kwargs['provider']
        data = {}
        for k,v in kwargs.items():
            data[k] = v
        __json = json.dumps(data, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __callback=handle_normalization)
        results = '''provider "{}" {}
            {}
{}
        '''.format(__provider, '{', __json, '}')
        return results


    def __renderResource(**kwargs):
        __resource = kwargs.get('resource')
        if (is_really_something(__resource, str)):
            del kwargs['resource']
        __name2 = kwargs.get('name2')
        if (is_really_something(__name2, str)):
            del kwargs['name2']
            kwargs['name'] = __name2
        data = {}
        for k,v in kwargs.items():
            data[k] = v
        __json = json.dumps(data, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __callback=handle_normalization)
        results = '''resource "{}" {} {}
            {}
{}
        '''.format(__resource, __name2, '{', __json, '}')
        return results


    def addProvider(self, provider='aws', region='us-east-2', callback=None):
        '''
            provider "aws" {
                region  = "eu-west-2" # this comes from the aws config files.
            }
        '''
        if (not callable(callback)):
            callback = TerraformFile.__renderProvider
        self['provider'] = self.section_named('provider', callback=callback, provider=provider, region=region)


    def addResource(self, resource='aws_ecr_repository', name='my_first_ecr_repo', callback=None):
        '''
            resource "aws_ecr_repository" "my_first_ecr_repo" {
                name = "my-first-ecr-repo" # Naming my repository
            }            
        '''
        if (not callable(callback)):
            callback = TerraformFile.__renderResource
        self[resource] = self.section_named('resource', callback=callback, resource=resource, name2=name)


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

if (__name__ == '__main__'):
    tf = TerraformFile()
    tf.addProvider(provider='aws', region='us-east-2')
    tf.addResource(resource='aws_ecr_repository', name='my_first_ecr_repo')
    tf.addResource(resource='aws_ecs_cluster', name='my_cluster')
    
    if (0):
        __env = get_environment_for_terraform_from('/home/raychorn/projects/python-projects/sample-docker-data/.env')
        __json = json.dumps(__env, cls=CompactJSONEncoder, indent=3, __replacements={':':'='}, __use_commas=False, __callback=handle_normalization)
        print(__json)

    print(tf.content)
    print('DONE!')