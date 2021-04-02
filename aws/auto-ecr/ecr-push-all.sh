#!/usr/bin/env bash

version=3.9
VENV=.venv
REQS=./requirements.txt

cpu_arch=$(uname -m)
echo "cpu_arch=$cpu_arch"

if [[ "$cpu_arch" != "x86_64" ]]
then
	echo "This script supports both x86_64 and ARM64 cpu architectures."
	#exit
fi

py1=$(which python$version)
echo "python$version is $py1"

myid=$(id -u)
echo "Your userid is $myid"
echo "Your userid is $EUID"

if [[ "$py1." == "." ]]
then
	if (( $EUID != 0 )); then
		echo "Please rerun this script as sudo to install the requirements."
		echo "After your run this script as sudo you will need to run it again without sudo to push your images to ECR."
		exit
	fi
    echo "\$py1 is empty which means Python is not installed."
    apt update -y
    apt install software-properties-common -y
    echo -ne '\n' | add-apt-repository ppa:deadsnakes/ppa
    apt install python3.9 -y
	apt install python3.9-distutils -y
	echo "All the requirements have been installed as sudo. Now you may restart this script to push your images to ECR."
	exit
fi

if (( $EUID == 0 )); then
	echo "Please rerun this script without sudo. All the requirements have been installed."
	exit
fi

py1=$(which python$version)
echo "python$version is $py1"

if [ -z "$py1" ]
then
	echo "Please rerun this script as sudo. The requirements have not been installed. Please install them."
	exit
else
    echo "Python v$version has been installed."
    py39=$(which python$version)
    echo "python$version is $py39"
    pypip3=$(which pip3)
    echo "Your pip3 is $pypip3"
	if [ -z "$pypip3" ]
	then
		echo "Installing pip3 locally."
		$py39 ./get-pip.py
		export PATH=/home/ubuntu/.local/bin:$PATH
		pypip3=$(which pip3)
		echo "Your pip3 is $pypip3"
	fi
    $pypip3 --version
    pipv=$($pypip3 list | grep virtualenv)
    echo "Your pip virtualenv status is $pipv"
	if [ -z "$pipv" ]
	then
		$pypip3 install virtualenv
	fi
    v=$($py39 -c 'import sys; i=sys.version_info; print("{}{}{}".format(i.major,i.minor,i.micro))')
    echo "Your $py39 specific version is $v"
    VENV=$VENV$v
    echo "VENV -> $VENV"
    if [[ -d $VENV ]]
    then
        rm -R -f $VENV
    fi
    if [[ ! -d $VENV ]]
    then
        virtualenv --python $py39 -v $VENV
    fi
    if [[ -d $VENV ]]
    then
        . ./$VENV/bin/activate
        pip install --upgrade pip

        if [[ -f $REQS ]]
        then
            pip install -r $REQS
        fi

    fi
fi

venv=$(ls ./.venv*/bin/activate)

if [[ -f $venv ]]
then
    . $venv
else
    echo "Cannot find $venv, please run this command in the correct directory."
    exit
fi

python ./auto_ecr.py --push-ecr
