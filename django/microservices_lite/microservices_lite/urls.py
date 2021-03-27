import os
import sys
from django.contrib import admin

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.conf.urls import handler404
from django.http import JsonResponse
from django.urls import include, path

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

assert os.environ.get('vyperlogix_lib3'), 'Cannot find the environment file.'

__is__ = False
fpath = os.path.dirname(__file__)
while (1):
    fp = os.sep.join([fpath, 'httpd.py'])
    if (fp == '/') or (os.path.exists(fp) and os.path.isfile(fp)):
        fpath = os.path.dirname(fp)
        __is__ = (os.path.exists(fp) and os.path.isfile(fp))
        break
    fpath = os.path.dirname(fpath)

__root = fpath
if (not any([f == __root for f in sys.path])):
    sys.path.insert(0, __root)

pylib3=os.environ.get('vyperlogix_lib3')
if (os.path.exists(pylib3)) and (not any([f == pylib3 for f in sys.path])):
    sys.path.insert(0, pylib3)

from libs import __catchall__ as catch_all

from libs import __utils__
logger = __utils__.get_logger()

from libs import __env__
m = sys.modules.get('libs.__env__')
assert m is not None, 'Cannot find "libs.__env__". Please resolve.'
f = getattr(m, 'read_env')
f(logger=logger)
__env__ = getattr(m, '__env__')

assert os.path.exists(__env__.get('plugins')), 'Missing the plugins path, check your .env file.'

__server_mode__ = __utils__.get_server_mode(environ=__env__)

is_serverMode_flask = lambda : __utils__.__is_serverMode_flask(__server_mode__)
is_serverMode_fastapi = lambda : __utils__.__is_serverMode_fastapi(__server_mode__)
is_serverMode_django = lambda : __utils__.__is_serverMode_django(__server_mode__)

from vyperlogix.iterators.dict import dictutils
from vyperlogix.plugins.services import ServiceRunnerLite as ServiceRunner

service_runner = ServiceRunner(__env__.get('plugins'), serverMode=__server_mode__, is_serverMode_flask=__utils__.__is_serverMode_flask, is_serverMode_fastapi=__utils__.__is_serverMode_fastapi, is_serverMode_django=__utils__.__is_serverMode_django, logger=logger, debug=False)

def django_response_handler(content, **kwargs):
    from django.http import JsonResponse
    return JsonResponse(content)

class MyView(View):
    
    def __catch_all__(self, path, request=None, response_handler=None, __json=None, logger=None, service_runner=None, is_serverMode_flask=None, __env__=None, is_debugging=False, dictutils=None):
        return catch_all.__catch_all__(path, request=request, response_handler=response_handler, __json=__json, logger=logger, service_runner=service_runner, is_serverMode_flask=is_serverMode_flask, is_serverMode_django=is_serverMode_django, __env__=__env__, is_debugging=is_debugging, dictutils=dictutils)
    
    def get(self, request, *args, **kwargs):
        return self.__catch_all__(request.path, request=request, logger=logger, service_runner=service_runner, is_serverMode_flask=is_serverMode_flask, __env__=__env__, response_handler=django_response_handler, dictutils=dictutils)

    def post(self, request, *args, **kwargs):
        return self.__catch_all__(request.path, request=request, logger=logger, service_runner=service_runner, is_serverMode_flask=is_serverMode_flask, __env__=__env__, response_handler=django_response_handler, dictutils=dictutils)
    
    def put(self, request, *args, **kwargs):
        return self.__catch_all__(request.path, request=request, logger=logger, service_runner=service_runner, is_serverMode_flask=is_serverMode_flask, __env__=__env__, response_handler=django_response_handler, dictutils=dictutils)

    def delete(self, request, *args, **kwargs):
        return self.__catch_all__(request.path, request=request, logger=logger, service_runner=service_runner, is_serverMode_flask=is_serverMode_flask, __env__=__env__, response_handler=django_response_handler, dictutils=dictutils)


from vyperlogix.django.django_utils import get_optionals
optionals = get_optionals(MyView.as_view(), num_url_parms=eval(os.environ.get('NUM_URL_PARMS', default=10)))

urlpatterns = [
    path('<slug:uuid>/', include(optionals) ),
    path('<slug:uuid>/', include(optionals) ),
    
    #path(r'^$', MyView.as_view()),
]

__root = os.path.dirname(os.path.dirname(__file__))
if (not any([f == __root for f in sys.path])):
    sys.path.insert(0, __root)

from microservices_lite.views import catchall
handler404 = catchall
