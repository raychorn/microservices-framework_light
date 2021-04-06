#!/usr/bin/env bash

if (( $EUID != 0 )); then
    echo "Please rerun this script as sudo or root to install terraform."
    exit
fi

cpu_arch=$(uname -m)

t=$(which terraform)

if [[ "$t." == "." ]]
then
    terraform_version="0.14.9"
    echo "Installing terraform version $terraform_version"
    apt update -y
    apt-get install wget unzip -y

    if [[ "$cpu_arch" == "x86_64" ]]
    then
        terraform_fname="terraform_$(echo $terraform_version)_linux_amd64"
    else
        terraform_fname="terraform_$(echo $terraform_version)_linux_arm64"
    fi

    echo "wget https://releases.hashicorp.com/terraform/$terraform_version/$terraform_fname.zip"
    wget https://releases.hashicorp.com/terraform/$terraform_version/$terraform_fname.zip

    if [[ -f $terraform_fname.zip ]]
    then
        echo "$terraform_fname.zip exists."
        unzip -o $terraform_fname.zip
    else
        echo "$terraform_fname.zip does not exist. Cannot proceed."
        exit
    fi

    if [[ -f "terraform" ]]
    then
        echo "terraform exists."
        mv terraform /usr/local/bin/
        rm -f $terraform_fname.zip*
    else
        echo "terraform does not exist. Cannot proceed."
        exit
    fi

    v=$(terraform -v)
    t=$(which terraform)
    if [[ "$t." == "." ]]
    then
        echo "Terraform has not been installed. Something went wrong."
    else
        echo "Terraform has been installed and is: $v."
    fi
else
    v=$(terraform -v)
    t=$(which terraform)
    if [[ "$t." == "." ]]
    then
        echo "Terraform has not been installed. Something went wrong."
    else
        echo "Terraform has been installed and is: $v."
    fi
fi


