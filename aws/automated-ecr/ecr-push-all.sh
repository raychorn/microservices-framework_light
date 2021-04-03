#!/usr/bin/env bash

version=3.9
VENV=
dir1=$(pwd)
WHO=$(whoami)

echo "Script name: $0"
echo "$# arguments "

if [[ "$1." == "--help." ]]
then
	echo "--verbose to make the output verbose for debugging purposes, if used this option must appear first."
	echo "--push-ecr to pushes all the Docker Images into ECR."
	echo "--clean-ecr to removes all repos from ECR."
	exit
fi

LOCAL_BIN=~/.local/bin
DIR0="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pDIR0=$(dirname "$DIR0")

REQS=$DIR0/requirements.txt

if [[ -f $REQS ]]
then
	if [[ "$1." == "--verbose." ]]
	then
		echo "REQS found in $REQS"
	fi
else
	REQS=$pDIR0/requirements.txt
fi

GETPIP=$DIR0/get-pip.py

if [[ -f $GETPIP ]]
then
	if [[ "$1." == "--verbose." ]]
	then
		echo "GETPIP found in $GETPIP"
	fi
else
	GETPIP=$pDIR0/get-pip.py
fi

if [[ "$1." == "--verbose." ]]
then
	echo "pDIR0=$pDIR0"
	echo "DIR0=$DIR0"
fi

is_root_user(){
	IS_ROOT=
	if [[ "$WHO." == "root." ]]
	then
		IS_ROOT=$WHO
	fi
}

is_root_user
if [[ "$1." == "--verbose." ]]
then
	echo "IS_ROOT=$IS_ROOT"
fi

cpu_arch=$(uname -m)
if [[ "$1." == "--verbose." ]]
then
	echo "cpu_arch=$cpu_arch"
	if [[ "$cpu_arch" != "x86_64" ]]
	then
		echo "This script supports both x86_64 and ARM64 cpu architectures."
	fi
fi

py1=$(which python$version)
if [[ "$1." == "--verbose." ]]
then
	echo "python$version is $py1"
fi

myid=$(id -u)
if [[ "$1." == "--verbose." ]]
then
	echo "Your userid is $EUID"
fi

if [[ "$py1." == "." ]]
then
	if (( $EUID != 0 )); then
		echo "Please rerun this script as sudo or root to install the requirements."
		echo "After your run this script as sudo you will need to run it again without sudo to push your images to ECR."
		exit
	fi
    echo "\$py1 is empty which means Python is not installed."
    apt update -y
    apt install software-properties-common -y
    echo -ne '\n' | add-apt-repository ppa:deadsnakes/ppa
    apt install python3.9 -y
	apt install python3.9-distutils -y
	echo "All the requirements have been installed as sudo or root. Now you may restart this script to push your images to ECR."
	exit
fi

py1=$(which python$version)
if [[ "$1." == "--verbose." ]]
then
	echo "python$version is $py1"
fi

if [ -z "$py1" ]
then
	echo "Please rerun this script as sudo or root. The requirements have not been installed. Please install them."
	exit
else
	if [[ "$1." == "--verbose." ]]
	then
		echo "Python v$version has been installed."
	fi
    py39=$(which python$version)
	if [[ "$1." == "--verbose." ]]
	then
		echo "python$version is $py39"
	fi
    pypip3=$(which $LOCAL_BIN/pip3)
	if [[ "$1." == "--verbose." ]]
	then
		echo "Your pip3 is $pypip3"
	fi
	if [ -z "$pypip3" ]
	then
		if [[ -d "$LOCAL_BIN" ]]
		then
			if [[ "$1." == "--verbose." ]]
			then
				echo "$LOCAL_BIN exists."
			fi
		else
			if [[ "$1." == "--verbose." ]]
			then
				echo "Installing pip3 locally."
			fi
			$py39 $GETPIP
		fi
		pypip3=$(which pip3)
		if [[ "$1." == "--verbose." ]]
		then
			echo "Your pip3 is $pypip3"
		fi
	fi
	export PATH=$LOCAL_BIN:$PATH
    $pypip3 --version
    pipv=$($pypip3 list | grep virtualenv)
	if [[ "$1." == "--verbose." ]]
	then
		echo "Your pip virtualenv status is $pipv"
	fi
	if [ -z "$pipv" ]
	then
		$pypip3 install virtualenv
	fi
    v=$($py39 -c 'import sys; i=sys.version_info; print("{}{}{}".format(i.major,i.minor,i.micro))')
	if [[ "$1." == "--verbose." ]]
	then
		echo "Your $py39 specific version is $v"
	fi
    VENV=$DIR0/.venv$v
	if [[ "$1." == "--verbose." ]]
	then
		echo "VENV -> $VENV"
	fi
	
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
        . $VENV/bin/activate
        pip install --upgrade pip

        if [[ -f $REQS ]]
        then
            pip install -r $REQS
        fi

    fi
fi

if [ -z "$VENV" ]
then
	VENV=$(ls $DIR0/.venv*/bin/activate)
	VENV=$(dirname "$VENV")
	VENV=$(dirname "$VENV")
fi

if [[ -d $VENV ]]
then
    . $VENV/bin/activate
else
    echo "Cannot find $VENV, please run this command in the correct directory."
    exit
fi

py39=$(which python$version)
if [[ "$1." == "--verbose." ]]
then
	echo "python$version is $py39"
fi
if [ -z "$py39" ]
then
	echo "Please rerun this script as sudo or root. The requirements have not been installed. Please install them."
	exit
fi

$py39 $DIR0/automated_ecr.py $1 $2 $3 $4 $5 $6 $7 $8 $9
