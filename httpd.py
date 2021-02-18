import os
import sys
from flask import Flask, request, Response

pylib = '/home/raychorn/projects/python-projects/private_vyperlogix_lib3'
if (not any([f == pylib for f in sys.path])):
    sys.path.insert(0, pylib)
    
from vyperlogix.env import environ
from vyperlogix.misc import _utils
from vyperlogix.decorators import expose
from vyperlogix.iterators.dict import dictutils
from vyperlogix.plugins.services import ServiceRunnerLite as ServiceRunner
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

is_debugging = __env__.get('debug', False)
is_debugging = True if (is_debugging) else False

app = Flask(__name__)

service_runner = ServiceRunner(__env__.get('plugins'), logger=None, debug=is_debugging)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'], defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    the_response = {"path": path}
    the_path = path.split('/')
    __fp_plugins__ = [__env__.get('plugins')]
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
            module_name = the_path[1]
            if (uuid == __env__.get('__uuid__')):
                if (module_name == '__directory__'):
                    if (uuid == __env__.get('__uuid__')):
                        the_response['fpath'] = os.path.dirname(__file__)
                        the_response['__plugins__'] = {}
                        for fp_plugins in __fp_plugins__:
                            the_response['__plugins__'][fp_plugins] = {}
                            the_response['__plugins__'][fp_plugins]['has_plugins'] = has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
                            if (not has_plugins):
                                os.mkdir(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['has_plugins'] = has_plugins = os.path.exists(fp_plugins) and os.path.isdir(fp_plugins)
                            fp_plugins_initpy = os.sep.join([fp_plugins, '__init__.py'])
                            if (not (os.path.exists(fp_plugins_initpy) and (os.path.isfile(fp_plugins_initpy)))):
                                with open(fp_plugins_initpy, 'w') as fOut:
                                    fOut.write('{}\n'.format('#'*40))
                                    fOut.write('# (c). Copyright, Vyper Logix Corp, All Rights Reserved.\n')
                                    fOut.write('{}\n'.format('#'*40))
                                    fOut.write('\n\n')
                                    fOut.flush()
                            if (is_debugging or request.args.get('DEBUG', False)):
                                the_response['__plugins__'][fp_plugins]['query_params'] = request.args
                                the_response['__plugins__'][fp_plugins]['modules'] = service_runner.modules.get(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['endpoints'] = expose.get_endpoints(for_root=fp_plugins)
                                the_response['__plugins__'][fp_plugins]['imports'] = service_runner.imports.get(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['aliases'] = service_runner.aliases.get(fp_plugins)
                                the_response['__plugins__'][fp_plugins]['status'] = 'OK'
                else:
                    d = None
                    func_name = the_path[2]
                    the_args = the_path[3:]
                    for root in __fp_plugins__:
                        endpoints = expose.get_endpoints(for_root=root).get(root, {})
                        d = endpoints.get(request.method, {})
                        if (module_name in list(service_runner.aliases.get(root, {}).keys())):
                            module_name = service_runner.aliases.get(root, {}).get(module_name)
                        if (module_name in list(service_runner.modules.get(root, {}).keys())):
                            fq_func_name = '{}.{}'.format(module_name, func_name)
                            d = d.get(fq_func_name, None)
                            if (d is not None) and (len(d) > 0):
                                break
                    if (d is not None):
                        data = {}
                        for k,v in request.args.items():
                            data[k] = v
                        for i in range(1, len(the_args)+1):
                            data['p{}'.format(i)] = the_args[i-1]
                        the_response['response'] = service_runner.exec(module_name, func_name, **data)
            else:
                return json.dumps({'success':False}), 404, {'ContentType':'application/json'}
        except Exception as ex:
            print(_utils.formattedException(details=ex))
    return Response(json.dumps(dictutils.json_cleaner(the_response)), mimetype='application/json')

if (__name__ == '__main__'):
    app.run(host=__env__.get('host', '127.0.0.1'), port=__env__.get('port', '5000'), load_dotenv=False, debug=False)
    