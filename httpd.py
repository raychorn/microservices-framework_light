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

from libs import __utils__
logger = __utils__.get_logger()

from libs import __env__
m = sys.modules.get('libs.__env__')
assert m is not None, 'Cannot find "libs.__env__". Please resolve.'
f = getattr(m, 'read_env')
f(logger=logger)
__env__ = getattr(m, '__env__')

import socket
os.environ['is_production'] = socket.gethostname() != 'DESKTOP-JJ95ENL'

assert os.path.exists(__env__.get('plugins')), 'Missing the plugins path, check your .env file.'


is_debugging = __env__.get('debug', False)
is_debugging = True if (is_debugging) else False

__server_mode__ = __utils__.get_server_mode(environ=__env__)

assert (__env__.get('use_flask', False)) or (__env__.get('use_fastapi', False)) or (__env__.get('use_django', False)), 'Must use either flask OR fastapi OR django so choose one of them, not none. Make a choice!'

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
            try:
                __json__ = await request.json()
            except:
                __json__ = {}
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
