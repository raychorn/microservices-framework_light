import os
import sys
from flask import Flask, request, Response
from flask.ext.runner import Runner

pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
if (not any([f == pylib for f in sys.path])):
    sys.path.insert(0, pylib)
    
from vyperlogix.env import environ
from vyperlogix.misc import _utils
from vyperlogix.decorators import expose
from vyperlogix.iterators.dict import dictutils
from vyperlogix.django.services import ServiceRunner
from vyperlogix.plugins import handler as plugins_handler

import mujson as json

__env__ = {}
env_literals = []
def get_environ_keys(*args, **kwargs):
    from expandvars import expandvars
    
    k = kwargs.get('key')
    v = kwargs.get('value')
    assert (k is not None) and (v is not None), 'Problem with kwargs -> {}, k={}, v={}'.format(kwargs,k,v)
    __logger__ = kwargs.get('logger')
    v = expandvars(v) if (k not in env_literals) else v
    environ = kwargs.get('environ', {})
    ignoring = __env__.get('IGNORING', '').split('|')
    environ[k] = str(v)
    if (k not in ignoring):
        __env__[k] = str(v)
    if (__logger__):
        __logger__.info('\t{} -> {}'.format(k, environ.get(k)))
    return True

env_path = './.env'
environ.load_env(env_path=env_path, environ=os.environ, cwd=env_path, verbose=True, logger=None, ignoring_re='.git|.venv|__pycache__', callback=lambda *args, **kwargs:get_environ_keys(args, **kwargs))

assert os.path.exists(__env__.get('plugins')), 'Missing the plugins path, check your .env file.'

__debug__ = False

app = Flask(__name__)
runner = Runner(app)

plugins_manager = plugins_handler.PluginManager(__env__.get('plugins'), debug=True, logger=None)
service_runner = plugins_manager.get_runner()

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'], defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    the_response = {"path": path}
    the_path = path.split('/')
    print('request.method -> {}'.format(request.method))
    if (request.method in ['POST', 'PUT', 'DELETE']):
        try:
            d = request.get_json()
            print(json.dumps(d, indent=3))
            print('-'*30)
        except Exception as ex:
            print(_utils.formattedException(details=ex))
            
    elif (request.method in ['GET']):
        try:
            the_response = {}
            uuid = the_path[0]
            func = the_path[1]
            if (func == '__directory__'):
                if (uuid == __env__.get('__uuid__')):
                    the_response['fpath'] = os.path.dirname(__file__)
                    __fp_plugins__ = __env__.get('plugins')
                    the_response['__fp_plugins__'] = {}
                    for fp_plugins in __fp_plugins__:
                        the_response['__fp_plugins__'][fp_plugins] = {}
                        the_response['__fp_plugins__'][fp_plugins]['has_plugins'] = has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
                        if (not has_plugins):
                            os.mkdir(fp_plugins)
                            the_response['__fp_plugins__'][fp_plugins]['has_plugins'] = has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
                        fp_plugins_initpy = os.sep.join([fp_plugins, '__init__.py'])
                        if (not (os.path.exists(fp_plugins_initpy) and (os.path.isfile(fp_plugins_initpy)))):
                            with open(fp_plugins_initpy, 'w') as fOut:
                                fOut.write('{}\n'.format('#'*40))
                                fOut.write('# (c). Copyright, Vyper Logix Corp, All Rights Reserved.\n')
                                fOut.write('{}\n'.format('#'*40))
                                fOut.write('\n\n')
                                fOut.flush()
                        runner = ServiceRunner(__fp_plugins__, logger=None, debug=__debug__)
                        if (__debug__ or request.args.get('DEBUG', False)):
                            the_response['__fp_plugins__'][fp_plugins]['query_params'] = request.args
                            the_response['__fp_plugins__'][fp_plugins]['modules'] = runner.modules.get(fp_plugins)
                            the_response['__fp_plugins__'][fp_plugins]['endpoints'] = expose.get_endpoints(for_root=fp_plugins)
                            the_response['__fp_plugins__'][fp_plugins]['imports'] = runner.imports.get(fp_plugins)
                            the_response['__fp_plugins__'][fp_plugins]['aliases'] = runner.aliases.get(fp_plugins)
                            the_response['__fp_plugins__'][fp_plugins]['status'] = 'OK'
        except Exception as ex:
            print(_utils.formattedException(details=ex))
    return Response(json.dumps(dictutils.json_cleaner(the_response)), mimetype='application/json')

if (__name__ == '__main__'):
    __help__ = '--help'
    sys.argv.append(__help__)
    if (not __help__ in sys.argv):
        if (not any([str(a).find('-p ') > -1 for a in sys.argv])):
            sys.argv.append('-p {}'.format(__env__.get('port')))
    runner.run()
    