from django.http import HttpResponse, HttpResponseNotFound

def catchall(request, exception):
    # ...
    return HttpResponseNotFound('<h1>Page not found</h1>')
