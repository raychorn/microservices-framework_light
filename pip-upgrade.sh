#!/bin/bash

VENV=$(ls .venv*/bin/activate)
REQS=./requirements.txt

VENV=$VENV$v
echo "VENV -> $VENV"

if [[ -f ./$VENV ]]
then
    . ./$VENV
    pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip3 install -U

fi