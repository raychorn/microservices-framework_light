# Dynamic Pluggable Microservice Framework - Light

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Contributing](../CONTRIBUTING.md)

## About <a name = "about"></a>

Based on Flask.

1. Not multi-tenant.
2. No Sandboxing.
3. No Database Support but you can roll your own.
4. No Security Support other than the __ID__ for each module which must appear in each URL.


## Getting Started <a name = "getting_started"></a>

No database support.  Uses IDs embedded in modules to determine which URLs to use.

### Prerequisites

pip install -r requirements.txt

### Installing

YOU are on your own but I believe if you and you can do this.

I can provide support when you provide a Sponsorship via the link.

## Usage <a name = "usage"></a>

```
sudo apt remove ca-certificates
sudo apt install ca-certificates
```

## Deployment

[deploy-flask-api-in-production-using-wsgi-gunicorn](https://www.javacodemonk.com/part-2-deploy-flask-api-in-production-using-wsgi-gunicorn-with-nginx-reverse-proxy-4cbeffdb)