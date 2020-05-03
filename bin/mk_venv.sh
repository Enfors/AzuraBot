#!/bin/bash

virtual_env_path="$HOME/venvs"

if [ ! -d $virtual_env_path ]; then
    mkdir -p $virtual_env_path
fi

cd $virtual_env_path

virtualenv -p /usr/bin/python3.7 AzuraBot

source AzuraBot/bin/activate
pip install --upgrade pip
pip install aiohttp botymcbotface
