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

from libs import __env__
m = sys.modules.get('libs.__env__')
assert m is not None, 'Cannot find "libs.__env__". Please resolve.'
f = getattr(m, 'read_env')
f()
__env__ = getattr(m, '__env__')

uvicorn.main("httpd:app", host="localhost", port=9999, reload=True)