#!/bin/bash

VENV=.venv
REQS=./requirements.txt

TARGET_PY="3.9"
LOCAL_BIN=~/.local/bin

DIR0="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

ARRAY=()

find_python(){
    pythons=$1
    PYTHONS=$(whereis $pythons)
    for val in $PYTHONS; do
        if [[ $val == *"/usr/bin/"* ]]; then
            if [[ $val != *"-config"* ]]; then
                ARRAY+=($val)
            fi
        fi
    done
}

pyenv="$HOME/.pyenv/bin/pyenv"

if [[ -f $pyenv ]]
then
    echo "1. Found $pyenv"
else
    echo "2. Installing pyenv"
    apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git -y
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    pyenv=$(which pyenv)

    if [[ -f $pyenv ]]
    then
        eval "$($pyenv init -)"
        eval "$($pyenv virtualenv-init -)"
    else
        echo "3. Cannot find pyenv."
    fi

    apt install pipenv -y

    echo "4. pyenv install --list"
    echo "5. pyenv virtualenv 3.9.4 .venv394"

fi

versions=$(pyenv versions --bare)

if [[ "$versions." == "." ]]
then
    for i in {9..1}; do 
        chk_vers=$(pyenv install --list | grep $TARGET_PY.$i)
        if [[ "$chk_vers." == "." ]]
        then
            echo ""
        else
            vers=$(echo "$TARGET_PY.$i")
            echo "6. Installing $vers"
            pyenv install $vers
            pyenv local $vers
            break
        fi
        echo "";
    done
fi

python39=$(which python3.9)

if [[ -f $python39 ]]
then
    echo "7. Found $python39"
else
    echo "8. Installing python3.9"
    apt update -y
    apt install software-properties-common -y
    echo -ne '\n' | add-apt-repository ppa:deadsnakes/ppa
    apt install python3.9 -y
	apt install python3.9-distutils -y
fi

python39=$(which python3.9)
pip3=$(which pip3)
setuptools="0"

if [[ -f $python39 ]]
then
    pip_local=$LOCAL_BIN/pip3
    if [[ -f $pip_local ]]
    then
        echo "8. Found $pip_local"
        export PATH=$LOCAL_BIN:$PATH
    else
        echo "Must install PIP?"
        if [[ -f $pip3 ]]
        then
            echo "9. $pip3 exists so not installing pip3, at this time."
        else
            echo "10. Installing pip3"
            GETPIP=$DIR0/get-pip.py

            if [[ -f $GETPIP ]]
            then
                $python39 $GETPIP
                export PATH=$LOCAL_BIN:$PATH
                pip3=$(which pip3)
                if [[ -f $pip3 ]]
                then
                    echo "11. Upgrading setuptools"
                    setuptools="1"
                    $pip3 install --upgrade setuptools > /dev/null 2>&1
                fi
            fi
        fi
    fi
fi

pip3=$(which pip3)
echo "12. pip3 is $pip3"

if [[ -f $pip3 ]]
then
    echo "13. Upgrading pip"
    $pip3 install --upgrade pip > /dev/null 2>&1
    if [[ "$setuptools." == "0." ]]
    then
        echo "14. Upgrading setuptools"
        $pip3 install --upgrade setuptools > /dev/null 2>&1
    fi
fi

#virtualenv=$(which virtualenv)
virtualenv=/usr/local/bin/virtualenv
echo "15. virtualenv is $virtualenv"

if [[ -f $virtualenv ]]
then
    $pip3 install virtualenv > /dev/null 2>&1
    $pip3 install --upgrade virtualenv > /dev/null 2>&1
fi

find_python python

pyston="/usr/bin/pyston3.8"

if [[ -f $pyston ]]
then
    echo "16. Found $pyston"
else
    apt-get install wget -y
    wget https://github.com/pyston/pyston/releases/download/v2.1/pyston_2.1_20.04.deb

    pyston_deb="$DIR0/pyston_2.1_20.04.deb"
    if [[ -f $pyston_deb ]]
    then
        apt install $pyston_deb -y
        rm -f $pyston_deb
    fi
fi

find_python pyston

#echo ${ARRAY[@]}
v=$($python39 sort.py "${ARRAY[@]}")
#echo "17. Use this -> $v"
ARRAY=()
ARRAY2=()
for val in $v; do
    ARRAY+=($val)
    x=$($val -c 'import sys; i=sys.version_info; print("{}.{}.{}".format(i.major,i.minor,i.micro))')
    ARRAY2+=("$val $x")
done
#echo ${ARRAY[@]}
#echo ${ARRAY2[@]}

PS3="Choose: "

select option in "${ARRAY2[@]}";
do
    echo "Selected number: $REPLY"
    choice=${ARRAY[$REPLY-1]}
    break
done

version=$($choice --version)
echo "Use this -> $choice --> $version"

v=$($choice -c 'import sys; i=sys.version_info; print("{}{}{}".format(i.major,i.minor,i.micro))')
vv=$($choice -c 'import sys; i=sys.version_info; print("{}.{}.{}".format(i.major,i.minor,i.micro))')
echo "Use this -> $choice --> $v -> $vv"

pyenv local $vv > /dev/null 2>&1

VENV=$VENV$v
echo "VENV -> $VENV"

if [[ -d $VENV ]]
then
    rm -R -f $VENV
fi

if [[ ! -d $VENV ]]
then
    echo "Making virtualenv for Python $choice -> $VENV"
    virtualenv --python $choice -v $VENV
fi

if [[ -d $VENV ]]
then
    . ./$VENV/bin/activate
    pip install --upgrade setuptools > /dev/null 2>&1
    pip install --upgrade pip > /dev/null 2>&1

    if [[ -f $REQS ]]
    then
        echo "Installing $REQS"
        pip install -r $REQS
    fi

fi