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

uvicorn.main("httpd:app", host="localhost", port=9999, reload=True)