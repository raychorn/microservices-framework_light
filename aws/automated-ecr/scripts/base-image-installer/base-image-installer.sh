#!/usr/bin/env bash

sudo apt install docker.io -y
sudo systemctl enable docker
sudo usermod -aG docker $USER
sudo systemctl status docker
sudo groupadd docker
sudo gpasswd -a $USER docker
newgrp docker
docker container run hello-world

cpu_arch=$(uname -m)

if [[ "$cpu_arch" != "x86_64" ]]
then
	sudo apt-get install docker-compose -y
else
	sudo curl -L "https://github.com/docker/compose/releases/download/1.28.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
	sudo chmod +x /usr/local/bin/docker-compose
fi
docker-compose --version
