# deploy this into /workspaces in the container

do_it(){
    REQS=requirements.txt

    dir1="."
    VENV=$dir1/.venv

    cd $dir1

    python=/usr/bin/python3.9
    vers=$($python -c 'import sys; i=sys.version_info; print("{}{}{}".format(i.major,i.minor,i.micro))')

    if [[ -d "$VENV$vers" ]]
    then
        echo "$VENV$vers exists"
    else
        echo virtualenv --python $python -v $VENV$vers
    fi

    vers2=$($python -c 'import sys; i=sys.version_info; print("{}{}".format(i.major,i.minor))')
    vyperlib=$dir1/python_lib3/vyperlogix$vers2.zip
    if [[ -f "$vyperlib" ]]
    then
        echo "$vyperlib exists"
    else
        vyperlib=/home/raychorn/projects/python-projects/private_vyperlogix_lib3
    fi

    cd $dir1
    export PYTHONPATH=$dir1:$vyperlib
    #ls -la
    #python -m debug1
    gunicorn -c $dir1/gunicorn/config.py --workers 4 --max-requests 1000 httpd:app
}

do_it #>./logs/runserver_report.txt 2>&1
