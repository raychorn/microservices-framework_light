#!/usr/bin/env bash

cd /tmp
mkdir @1
cd @1

cpu_arch=$(uname -m)

curl "https://awscli.amazonaws.com/awscli-exe-linux-$cpu_arch.zip" -o "awscliv2.zip"
sudo apt-get install unzip zip -y
echo -ne 'A' | unzip awscliv2.zip

aws_cli_current=/usr/local/aws-cli/v2/current
if [[ -d $aws_cli_current ]]
then
	echo "Updating the current aws cli."
	sudo ./aws/install --update
else
	echo "Installing the current aws cli."
	sudo ./aws/install
fi

aws_version=$(aws --version)

if [[ "$aws_version" == "." ]]
then
	echo "aws cli has not been installed."
else
	echo "aws cli has been installed :: $aws_version."
fi
