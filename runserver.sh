#!/usr/bin/env bash

HOSTNAME=$(cat /proc/sys/kernel/hostname)

dir0=".."
dir1="."

if [ "$HOSTNAME" != "DESKTOP-JJ95ENL" ]
then
    echo "Running via host-name $HOSTNAME and this seems to be Production."
    dir0="/workspaces"
    dir1="$dir0/microservices-framework"
    NGINX=$(which nginx)
    if [[ -f "$NGINX" ]]
    then
        echo "$NGINX exists"
    else
        echo "NGINX does not exist, so installing it."
        sudo apt install nginx -y
        NGINX=$(which nginx)
        if [[ -f "$NGINX" ]]
        then
            echo "$NGINX exists"
        else
            echo "NGINX does not exist, so cannot continue."
            exit
        fi
    fi
    NGINX_REVERSE_PROXY="/etc/nginx/sites-available/reverse-proxy.conf"
    if [[ -f "$NGINX_REVERSE_PROXY" ]]
    then
        echo "$NGINX_REVERSE_PROXY exists"
    else
        echo "NGINX_REVERSE_PROXY does not exist, so putting it in-place."
        NGINX_REVERSE_PROXY_SRC="$dir1/etc/nginx/sites-available/reverse-proxy.conf"
        if [[ -f "$NGINX_REVERSE_PROXY_SRC" ]]
        then
            echo "$NGINX_REVERSE_PROXY_SRC exists"
            cp $NGINX_REVERSE_PROXY_SRC $NGINX_REVERSE_PROXY
        else
            echo "NGINX_REVERSE_PROXY_SRC does not exist, so cannot continue."
            exit
        fi
    fi
    SYMBOLIC_LINK=$(ls -la /etc/nginx/sites-enabled | grep reverse-proxy.conf)
    if [ -z "$SYMBOLIC_LINK" ]
    then
        sudo systemctl stop nginx
        sudo unlink /etc/nginx/sites-enabled/default
        sudo ln -s /etc/nginx/sites-available/reverse-proxy.conf /etc/nginx/sites-enabled/default
        sudo systemctl start nginx
    fi
fi

set -a; source $dir1/.env; set +a

do_it(){
    REQS=requirements.txt

    VENV=$dir1/.venv

    cd $dir1

    python=$(which python3.9)
    vers=$($python -c 'import sys; i=sys.version_info; print("{}{}{}".format(i.major,i.minor,i.micro))')
    VENVvers=$(ls $VENV$vers)
    echo "VENV$vers=$VENV$vers"
    echo "VENVvers=$VENVvers"

    if [ -z "$VENVvers" ]
    then
        ENVS=$(ls -d .venv*)
        for val in $ENVS; do
            echo "Removing $val"
            rm -R -f $val
        done
        virtualenv --python $python -v $VENV$vers
        . $VENV$vers/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo "$VENV$vers exists"
        . $VENV$vers/bin/activate
        pip install --upgrade pip
        pip --version
    fi

    vers2=$($python -c 'import sys; i=sys.version_info; print("{}{}".format(i.major,i.minor))')
    vyperlib=$(ls $dir1/python_lib3 | grep "cannot access")
    if [ -z "$vyperlib" ]
    then
        PYLIB=$(ls -d $dir0/private_vyperlogix_lib3)
        echo "PYLIB=$PYLIB"
        if [ ! -z "$PYLIB" ]
        then
            echo "PYLIB=$PYLIB exists"
        fi
        vyperlib=$PYLIB
    else
        vyperlib=$(ls $dir1/python_lib3)
        echo "$vyperlib exists"
        vyperlib=$vyperlib/vyperlogix$vers2.zip
        if [[ -f "$vyperlib" ]]
        then
            echo "$vyperlib exists"
        else
            echo "$vyperlib does not exist"
            exit
        fi
    fi

    cd $dir1
    export PYTHONPATH=$dir1:$vyperlib
    echo "PYTHONPATH=$PYTHONPATH"

    echo "use_flask=$use_flask"
    if [ "$use_flask" = "True" ]
    then
        echo "use_flask !!!"
        gunicorn -c $dir1/gunicorn/config.py httpd:app # --max-requests 1000
    fi
    echo "use_fastapi=$use_fastapi"
    if [ "$use_fastapi" = "True" ]
    then
        echo "use_fastapi !!!"
        python $dir1/httpd.py
    fi
    echo "use_django=$use_django"
    if [ "$use_django" = "True" ]
    then
        echo "use_django !!!"
        cd $dir1/django/microservices_lite
        python manage.py runserver
    fi
}

do_it #>./logs/runserver_report.txt 2>&1
