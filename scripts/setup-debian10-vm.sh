#!/bin/bash
set -e

# Common packages
sudo apt install git

# Install docker
# Optionally: remove all
# sudo apt-get purge docker lxc-docker docker-engine docker.io
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian buster stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
echo "### DOCKER STATUS ###"
docker -v
sudo systemctl --no-pager status docker

# Add the current user to the docker group to make life easier.
sudo usermod -a -G docker $USER
