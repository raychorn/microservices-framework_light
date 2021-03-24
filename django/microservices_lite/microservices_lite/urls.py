import os
import sys
from django.contrib import admin
from django.urls import include, path

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.conf.urls import handler404
from django.http import JsonResponse

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

from libs import __catchall__ as catch_all

pylib3=os.environ.get('vyperlogix_lib3')
if (os.path.exists(pylib3)) and (not any([f == pylib3 for f in sys.path])):
    sys.path.insert(0, pylib3)

    
class MyView(View):
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def put(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def delete(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
from vyperlogix.django.django_utils import get_optionals

optionals = get_optionals(MyView.as_view(), num_url_parms=eval(os.environ.get('NUM_URL_PARMS', default=10)))

urlpatterns = [
    path('<slug:uuid>/', include(optionals) ),
    path('<slug:uuid>/', include(optionals) ),
    
    #path(r'^$', MyView.as_view()),
]

from views import  catchall
handler404 = catchall
