# deploy this into /workspaces in the container

do_it(){
    REQS=requirements.txt

    dir1="."
    VENV=$dir1/.venv

    cd $dir1

    python=/usr/bin/python3.9
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
        . ./$VENV$vers/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo "$VENV$vers exists"
        . ./$VENV$vers/bin/activate
        pip install --upgrade pip
        pip --version
    fi

    vers2=$($python -c 'import sys; i=sys.version_info; print("{}{}".format(i.major,i.minor))')
    vyperlib=$(ls $dir1/python_lib3 | grep "cannot access")
    if [ -z "$vyperlib" ]
    then
        PYLIB=$(ls -d ../private_vyperlogix_lib3)
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
    #ls -la
    #python -m debug1
    gunicorn -c $dir1/gunicorn/config.py --workers 4 httpd:app # --max-requests 1000
}

do_it #>./logs/runserver_report.txt 2>&1
