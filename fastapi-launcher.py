import os
import sys
import uvicorn

'''
    {
        "name": "Python: FastAPI",
        "type": "python",
        "request": "launch",
        "module": "uvicorn",
        "env": {
            "host_server": "localhost",
            "ssl_mode": "prefer",
        },
        "args": [
            "httpd:app",
            "--reload",
            "--port",
            "9999"
        ]
    }
'''

if (os.environ.get('libs')):
    pylibs = os.environ.get('libs')
    if (not any([f == pylibs for f in sys.path])):
        sys.path.insert(0, pylibs)

if (os.environ.get('vyperlogix_lib3')):
    pylib = os.environ.get('vyperlogix_lib3')
    if (not any([f == pylib for f in sys.path])):
        sys.path.insert(0, pylib)
    

from libs import __env__
m = sys.modules.get('libs.__env__')
assert m is not None, 'Cannot find "libs.__env__". Please resolve.'
f = getattr(m, 'read_env')
f()
__env__ = getattr(m, '__env__')

__host__ = __env__.get('host', 'localhost')
__port__ = eval(__env__.get('port', 9999))
assert isinstance(__host__, str), 'What, no host name?  Please fix.'
assert isinstance(__port__, int), 'What, no port number?  Please fix.'

uvicorn.run("httpd:app", host=__host__, port=__port__, reload=True)