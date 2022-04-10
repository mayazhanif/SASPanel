#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
username=$1
croncommand=$2
mkdir -m 777 -p /home/$username/crobjobs/logs
chown -R www-data:www-data /home/$username/crobjobs/logs/*
chown -R $username:$username /home/$username/crobjobs/logs/*
echo $croncommand >> mycron
crontab -u $username mycron
rm mycron