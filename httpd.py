import os
import sys
import enum
import asyncio

from datetime import datetime

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

pylibs = os.environ.get('libs', os.sep.join([os.path.dirname(__file__), 'libs'])).replace('.{}'.format(os.sep), os.path.dirname(__file__)+os.sep)
if (os.path.exists(pylibs)):
    if (not any([f == pylibs for f in sys.path])):
        sys.path.insert(0, pylibs)

pylib = os.environ.get('vyperlogix_lib3', os.sep.join([os.path.dirname(os.path.dirname(__file__)), 'private_vyperlogix_lib3']))
if (os.path.exists(pylib)):
    if (not any([f == pylib for f in sys.path])):
        sys.path.insert(0, pylib)

from vyperlogix.misc import _utils
from vyperlogix.decorators import expose
from vyperlogix.iterators.dict import dictutils
from vyperlogix.plugins.services import ServiceRunnerLite as ServiceRunner
from vyperlogix.plugins import handler as plugins_handler

import mujson as json

logger = None

if (0):
    import logging
    from logging.handlers import RotatingFileHandler
    
    is_really_something = lambda s,t:s and t(s)
    something_greater_than_zero = lambda s:(s > 0)

    default_timestamp = lambda t:t.isoformat().replace(':', '').replace('-','').split('.')[0]

    is_uppercase = lambda ch:''.join([c for c in str(ch) if c.isupper()])

    def get_stream_handler(streamformat="%(asctime)s:%(levelname)s:%(message)s"):
        stream = logging.StreamHandler()
        stream.setLevel(logging.INFO)
        stream.setFormatter(logging.Formatter(streamformat))
        return stream

        
    def setup_rotating_file_handler(logname, logfile, max_bytes, backup_count):
        assert is_really_something(backup_count, something_greater_than_zero), 'Missing backup_count?'
        assert is_really_something(max_bytes, something_greater_than_zero), 'Missing max_bytes?'
        ch = RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
        l = logging.getLogger(logname)
        l.addHandler(ch)
        return l

    production_token = 'production'

    base_filename = os.path.splitext(os.path.basename(__file__))[0]

    log_filename = '{}{}{}{}{}{}{}_{}.log'.format('logs', os.sep, base_filename, os.sep, production_token, os.sep, base_filename, default_timestamp(datetime.utcnow()))

    if not os.path.exists(os.path.dirname(log_filename)):
        os.makedirs(os.path.dirname(log_filename))

    if (os.path.exists(log_filename)):
        os.remove(log_filename)

    log_format = ('[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        filename=(log_filename),
    )

    logger = setup_rotating_file_handler(base_filename, log_filename, (1024*1024*1024), 10)
    logger.addHandler(get_stream_handler())
else:
    from libs import __utils__
    logger = __utils__.get_logger()

from libs import __env__
m = sys.modules.get('libs.__env__')
assert m is not None, 'Cannot find "libs.__env__". Please resolve.'
f = getattr(m, 'read_env')
f(logger=logger)
__env__ = getattr(m, '__env__')

assert os.path.exists(__env__.get('plugins')), 'Missing the plugins path, check your .env file.'


is_debugging = __env__.get('debug', False)
is_debugging = True if (is_debugging) else False

if (0):
    class ServerMode(enum.Enum):
        use_none = 0
        use_flask = 1
        use_fastapi = 2
        use_django = 4

    __server_mode__ = ServerMode.use_none
    if (__env__.get('use_flask', False)):
        __server_mode__ = ServerMode.use_flask
        assert not __env__.get('use_fastapi', False), 'Cannot use flask and fastapi so choose one of them, not more than one.'
        assert not __env__.get('use_django', False), 'Cannot use both flask and django so choose one of them, not more than one.'

    if (__env__.get('use_fastapi', False)):
        __server_mode__ = ServerMode.use_fastapi
        assert not __env__.get('use_flask', False), 'Cannot use both flask and fastapi so choose one of them, not more than one.'
        assert not __env__.get('use_django', False), 'Cannot use both fastapi and django so choose one of them, not more than one.'

    if (__env__.get('use_django', False)):
        __server_mode__ = ServerMode.use_django
        assert not __env__.get('use_flask', False), 'Cannot use both flask and django so choose one of them, not more than one.'
        assert not __env__.get('use_fastapi', False), 'Cannot use both fastapi and django so choose one of them, not more than one.'
else:
    __server_mode__ = __utils__.get_server_mode(environ=__env__)

if (0):
    def is_running_fastapi_correctly():
        import inspect
        stack = inspect.stack()
        for fr in stack:
            if (fr.filename.find('fastapi-launcher') > -1):
                return True
        return False

    if (__env__.get('use_flask', False)):
        assert is_running_fastapi_correctly() == False, 'You must not use the "fastapi-launcher.py" to run this framework with "use_flask=True".  Please get it together.'

    if (__env__.get('use_fastapi', False)):
        assert is_running_fastapi_correctly() == True, 'You must use the "fastapi-launcher.py" to run this framework with "use_fastapi=True".  Please get it together.'


assert (__env__.get('use_flask', False)) or (__env__.get('use_fastapi', False)) or (__env__.get('use_django', False)), 'Must use either flask OR fastapi OR django so choose one of them, not none. Make a choice!'

if (0):
    __is_serverMode_flask = lambda sm: sm == ServerMode.use_flask
    __is_serverMode_fastapi = lambda sm: sm == ServerMode.use_fastapi
    __is_serverMode_django = lambda sm: sm == ServerMode.use_django

is_serverMode_flask = lambda : __utils__.__is_serverMode_flask(__server_mode__)
is_serverMode_fastapi = lambda : __utils__.__is_serverMode_fastapi(__server_mode__)
is_serverMode_django = lambda : __utils__.__is_serverMode_django(__server_mode__)

if (is_serverMode_flask()):
    from flask import Flask, request, Response
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)

if (is_serverMode_fastapi()):
    from typing import Union
    from fastapi import FastAPI
    from pydantic import ValidationError
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError

    from starlette.exceptions import HTTPException
    from starlette.middleware.cors import CORSMiddleware
    from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_200_OK

    def get_application(title=__name__, debug=None, version=None):
        application = FastAPI(title=title, debug=debug, version=version)

        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
            return JSONResponse({"errors": [exc.detail]}, status_code=exc.status_code)        

        async def http422_error_handler(
            _: Request, exc: Union[RequestValidationError, ValidationError],
        ) -> JSONResponse:
            return JSONResponse(
                {"errors": exc.errors()}, status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )

        application.add_exception_handler(HTTPException, http_error_handler)
        application.add_exception_handler(RequestValidationError, http422_error_handler)

        return application 
    app = get_application(title=__name__, debug=False, version='2.1.0')

service_runner = ServiceRunner(__env__.get('plugins'), serverMode=__server_mode__, is_serverMode_flask=__utils__.__is_serverMode_flask, is_serverMode_fastapi=__utils__.__is_serverMode_fastapi, logger=logger, debug=is_debugging)

from libs import __catchall__ as catch_all

if (0):
    def __catch_all__(path, request=None, service_runner=None, response_handler=None, __json=None):
        the_path = [p for p in path.split('/') if (len(str(p)) > 0)]
        the_response = {"path": '/'.join(the_path[1:])}
        __fp_plugins__ = [__env__.get('plugins')]
        print('request.method -> {}'.format(request.method))
        if (request.method in ['POST', 'PUT', 'DELETE']):
            try:
                uuid = the_path[0] if (len(the_path) > 0) else None
                if (uuid == __env__.get('__uuid__')):
                    d = request.get_json() if (is_serverMode_flask()) else __json
                    logger.info(json.dumps(d, indent=3))
                    logger.info('-'*30)
                    d = service_runner.resolve(request, data=d, path=the_path, plugins=__fp_plugins__)
                    if (d is not None):
                        the_response['response'] = d
                    else:
                        return json.dumps({'success':False}), 404, {'ContentType':'application/json'}
                else:
                    return json.dumps({'success':False}), 404, {'ContentType':'application/json'}
            except Exception as ex:
                logger.exception('EXCEPTION -> {}'.format(request.method), ex)
                return json.dumps({'success':False, 'reason': str(ex)}), 404, {'ContentType':'application/json'}
                
        elif (request.method in ['GET']):
            try:
                the_response = {}
                uuid = the_path[0] if (len(the_path) > 0) else None
                module_name = the_path[1] if (len(the_path) > 1) else None
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
                                if (is_debugging or (request.args if (is_serverMode_flask()) else request.query_params).get('DEBUG', False)):
                                    the_response['__plugins__'][fp_plugins]['query_params'] = request.args if (is_serverMode_flask()) else request.query_params
                                    the_response['__plugins__'][fp_plugins]['modules'] = service_runner.modules.get(fp_plugins)
                                    the_response['__plugins__'][fp_plugins]['endpoints'] = expose.get_endpoints(for_root=fp_plugins)
                                    the_response['__plugins__'][fp_plugins]['imports'] = service_runner.imports.get(fp_plugins)
                                    the_response['__plugins__'][fp_plugins]['aliases'] = service_runner.aliases.get(fp_plugins)
                                    the_response['__plugins__'][fp_plugins]['status'] = 'OK'
                    else:
                        d = service_runner.resolve(request, path=the_path, plugins=__fp_plugins__)
                        if (d is not None):
                            the_response['response'] = d
                        else:
                            return json.dumps({'success':False}), 404, {'ContentType':'application/json'}
                else:
                    return json.dumps({'success':False}), 404, {'ContentType':'application/json'}
            except Exception as ex:
                logger.exception('EXCEPTION -> {}'.format(request.method), ex)
                return json.dumps({'success':False, 'reason': str(ex)}), 404, {'ContentType':'application/json'}
        __response__ = None
        if (callable(response_handler)):
            try:
                __response__ = response_handler(json.dumps(dictutils.json_cleaner(the_response)), mimetype='application/json')
            except:
                pass
        return __response__

if (is_serverMode_flask()):
    def flask_response_handler(content, **kwargs):
        return Response(content, **kwargs)
    
    @app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'], defaults={'path': ''})
    @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def flask_catch_all(path):
        return catch_all.__catch_all__(path, request=request, response_handler=flask_response_handler, service_runner=service_runner, logger=logger, is_serverMode_flask=is_serverMode_flask, __env__=__env__, is_debugging=is_debugging, dictutils=dictutils)
    
if (is_serverMode_fastapi()):
    def fastapi_response_handler(content, **kwargs):
        return JSONResponse(
            json.loads(content), status_code=HTTP_200_OK,
        )
    
    @app.route("/{full_path:path}", methods=['GET', 'POST', 'PUT', 'DELETE'])
    async def fastapi_catch_all(request):
        __json__ = None
        if (request.method in ['POST', 'PUT', 'DELETE']):
            __json__ = await request.json()
        return catch_all.__catch_all__(request['path'], request=request, response_handler=fastapi_response_handler, service_runner=service_runner, __json=__json__, logger=logger, is_serverMode_flask=is_serverMode_flask, __env__=__env__, is_debugging=is_debugging, dictutils=dictutils)

if (__name__ == '__main__'):

    if (is_serverMode_flask()):    
        app.run(host=__env__.get('host', '127.0.0.1'), port=__env__.get('port', '5000'), load_dotenv=False, debug=False)
    
    if (is_serverMode_fastapi()):
        import uvicorn

        __host__ = __env__.get('host', 'localhost')
        __port__ = eval(__env__.get('port', 9999))
        assert isinstance(__host__, str), 'What, no host name?  Please fix.'
        assert isinstance(__port__, int), 'What, no port number?  Please fix.'

        async def run(app=None, host=None, port=None, reload=None, logger=None):
            import multiprocessing
            __workers__ = (multiprocessing.cpu_count() * 2) + 1
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                reload=reload,
                workers=__workers__,
                access_log=logger)
            server = uvicorn.Server(config=config)
            server.install_signal_handlers = lambda: None
            await server.serve() 

        asyncio.run(run(app=app, host=__host__, port=__port__, reload=True, logger=logger))
