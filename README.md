# Dynamic Pluggable Microservice Framework - Light

## Table of Contents

- [Dynamic Pluggable Microservice Framework - Light](#dynamic-pluggable-microservice-framework---light)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
    - [Web Framework Agnostic for Flask, Django or FastAPI](#web-framework-agnostic-for-flask-django-or-fastapi)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installing](#installing)
      - [Main .env](#main-env)
        - [__LITERALS__](#literals)
        - [Sample .env file](#sample-env-file)
      - [Docker .env](#docker-env)
  - [Usage](#usage)
  - [Deployment](#deployment)
    - [Docker](#docker)
    - [nginx reverse-proxy](#nginx-reverse-proxy)
    - [Terraform](#terraform)
      - [AWS ECR](#aws-ecr)
      - [AWS ECS](#aws-ecs)

## About
[ToC](#table-of-contents)

Based on Flask.

1. Not multi-tenant.
2. No Sandboxing.
3. No Database Support but you can roll your own.
4. No Security Support other than the __ID__ for each module which must appear in each URL.

### Web Framework Agnostic for Flask, Django or FastAPI

[ToC](#table-of-contents)

1. Works with Flask and gunicorn.
2. Works with FastAPI and uvicorn.
3. Works with Django and wsgi or whatever else Django supports for deployment.

* Flask supports gunicorn. (see runserver.sh)
* FastAPI support uvicorn (see runserver.sh)
* Django support wsgi but you are on your own for this one.


## Getting Started

[ToC](#table-of-contents)

No database support.  Uses IDs embedded in modules to determine which URLs to use.

### Prerequisites

[ToC](#table-of-contents)

pip install -r requirements.txt

### Installing

[ToC](#table-of-contents)

YOU are on your own but I believe if you and you can do this.

I can provide support when you provide a Sponsorship via the link.

#### Main .env

[ToC](#table-of-contents)

##### __LITERALS__

Literals are defined using Python Syntax as follows:

```
__LITERALS__="['MONGO_INITDB_ROOT_PASSWORD']"
```

##### Sample .env file

```
plugins=/home/raychorn/projects/python-projects/private_microservice_plugins1

__uuid__=your-uuid-goes-here-matches-uuid-in-your-modules

__LITERALS__="['MONGO_INITDB_ROOT_PASSWORD']"
__EVALS__="use_flask|use_fastapi|use_django"
use_flask=False
use_fastapi=True
use_django=False

host=0.0.0.0
port=9999
VYPERAPI_URL=$host:$port

LOGGER_NAME=vyperapi

MONGO_INITDB_DATABASE=admin
MONGO_HOST=your-ip-address-or-dns-name
MONGO_PORT=27017
MONGO_URI=mongodb://$MONGO_HOST:$MONGO_PORT/?connectTimeoutMS=300000
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=your-mongodb-password-goes-here
MONGO_AUTH_MECHANISM=SCRAM-SHA-256

MONGO_OVERRIDE=True

debug=1

libs=./libs
vyperlogix_lib3=/home/raychorn/projects/python-projects/private_vyperlogix_lib3

gunicorn_backlog=2048
gunicorn_workers=3
gunicorn_threads=3
gunicorn_worker_class=sync # https://docs.gunicorn.org/en/latest/settings.html#worker-class
gunicorn_worker_connections=1000
gunicorn_timeout=180
gunicorn_keepalive=10
gunicorn_graceful_timeout=30
gunicorn_pidfile=./gunicorn/gunicorn.pid
gunicorn_daemon=False
gunicorn_errorlog=./gunicorn/error.log
gunicorn_loglevel=info
gunicorn_accesslog=./gunicorn/access.log
gunicorn_proc_name=vyperapi

NUM_URL_PARMS=250 # do not exceed 250
```

#### Docker .env

[ToC](#table-of-contents)

```
# MongoDB
MONGO_URL=mongodb://mongodb:27017
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=provide-your-own-database
MONGO_INITDB_DATABASE=admin
MONGO_REPLICA_SET_NAME=rs0
MONGO_AUTH_MECHANISM=SCRAM-SHA-256

ADMIN_ID=4a1bf01e-0693-48c5-a52b-fc275205c1d8
SECRETS=
PYTHONPATH=.:/workspaces/microservices-framework/microservices-framework/python_lib3/vyperlogix38.zip:/workspaces/microservices-framework/microservices-framework/.venv387/lib/python3.8/site-packages
VYPERAPI_URL=10.5.0.6:9000
plugins=.:/workspaces/plugins/admin-plugins # dot means the default, all others delimited by ":" adds more directories to the list.
```

## Usage

[ToC](#table-of-contents)

```
sudo apt remove ca-certificates
sudo apt install ca-certificates
```

## Deployment

[ToC](#table-of-contents)

[deploy-flask-api-in-production-using-wsgi-gunicorn](https://www.javacodemonk.com/part-2-deploy-flask-api-in-production-using-wsgi-gunicorn-with-nginx-reverse-proxy-4cbeffdb)

### Docker

* See the docker directory in this project for hints.

### nginx reverse-proxy

* see also etc/nginx and associated config files.

[how-to-install-nginx-on-ubuntu-20-04](https://phoenixnap.com/kb/how-to-install-nginx-on-ubuntu-20-04)

```
sudo apt-get update -y
sudo apt-get install nginx -y
nginx -v
```

### Terraform

* See also auto-terraform.sh

#### AWS ECR

* See the auto-ecr.sh.

#### AWS ECS

* Deployments via auto-terraform.sh

