"""microservices_lite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
import sys
from django.contrib import admin
from django.urls import path

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View

from django.http import JsonResponse

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
module_name = fpath.split(os.sep)[-1]
if (not any([f ==__root > -1 for f in sys.path])):
    sys.path.insert(0, __root)

    
class MyView(View):

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': form})
    
    def put(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': form})

    def delete(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': form})
    
urlpatterns = [
    #path('admin/', admin.site.urls),
    path(r'.*', MyView.as_view())
]
