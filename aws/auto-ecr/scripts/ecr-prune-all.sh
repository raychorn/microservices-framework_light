#!/usr/bin/env bash

venv=$(ls ./.venv*/bin/activate)

if [[ -f $venv ]]
then
    . $venv
else
    echo "Cannot find $venv, please run this command in the correct directory."
    exit
fi

python ./auto_ecr.py --clean-ecr
