# Dynamic Pluggable Microservice Framework - Light

## Table of Contents

- [Dynamic Pluggable Microservice Framework - Light](#dynamic-pluggable-microservice-framework---light)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
    - [Web Framework Agnostic for Flask, Django or FastAPI](#web-framework-agnostic-for-flask-django-or-fastapi)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installing](#installing)
      - [Docker .env](#docker-env)
  - [Usage](#usage)
  - [Deployment](#deployment)
    - [Docker](#docker)
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

### Terraform

* See also auto-terraform.sh

#### AWS ECR

* See the auto-ecr.sh.

#### AWS ECS

* Deployments via auto-terraform.sh

