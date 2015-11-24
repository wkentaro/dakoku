#!/bin/bash

set -e

OS=`uname -s`

echo "install requirements..."
if [ $OS = "Linux" ]; then
    sudo apt-get update
    sudo apt-get install curl python-pip xvfb
elif [ $OS = "Darwin" ]; then
    brew install xvfb
else
    echo "Only supports OSX/Ubuntu"
    exit 1
fi

echo "install python modules..."
PIP="pip"
if [ $OS = "Linux" ]; then
    PIP="sudo -H pip"
fi
$PIP install -U pip
$PIP install -U pytz APScheduler
$PIP install -U splinter
$PIP install 'japanese-holiday==0.0.4'


echo "setup nodejs..."
if [ ! -e $HOME/.nvm ]; then
    curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.25.4/install.sh | bash
fi
source $HOME/.nvm/nvm.sh
nvm install 0.12.2
nvm alias default 0.12.2

if [ "`which npm`" = ""]; then
    echo "failed to install nvm, please install manually"
    exit 1
fi
npm install -g pm2

echo "All setup is done."
echo "Now let's edit config.sample and schedule.sample"
