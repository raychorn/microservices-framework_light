#!/usr/bin/env bash

set -a; source .env; set +a

if [[ -f "$gunicorn_pidfile" ]]
then
    echo "$gunicorn_pidfile exists"
    pid=$(cat $gunicorn_pidfile)
    kill -9 $pid
else
    echo "$gunicorn_pidfile does not exist"
fi
