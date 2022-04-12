#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
domain=$1
email=$2
certbot run -n --nginx --non-interactive --agree-tos -d $domain,www.$domain  -m  $email  --redirect