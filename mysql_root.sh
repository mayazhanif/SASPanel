#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
username=$1
domain=$2

# Functions
ok() { echo -e '\e[32m'$domain'\e[m'; } # Green
die() { echo -e '\e[1;31m'$domain'\e[m'; exit 1; }


# Variables
#NGINX_AVAILABLE_VHOSTS='/etc/nginx/sites-available'
NGINX_ENABLED_VHOSTS='/etc/nginx/conf.d'
WEB_DIR='/home'
WEB_USER=$username

LOG_DIR = $WEB_DIR/$WEB_USER/logs
DOMAIN_DIR = $WEB_DIR/$WEB_USER/domains/$domain/public_html

mkdir -p $LOG_DIR
mkdir -p $DOMAIN_DIR

# Sanity check
[ $(id -g) != "0" ] && die "Script must be run as root."
#[ $# != "1" ] && die "Usage: $(basename $0) domainName"

# Create nginx config file
cat > $NGINX_ENABLED_VHOSTS/$domain-vhost.conf <<EOF
### www to non-www
#server {
#    listen	 80;
#    server_name  www.$domain;
#    return	 301 http://$domain\$request_uri;
#}

server {
    listen   80;
    server_name $domain www.$domain;
    root  $DOMAIN_DIR;
    charset  utf-8;
    index index.php index.html index.htm;

    access_log $LOG_DIR/$domain-access.log;
    #access_log off;

    error_log $LOG_DIR/$domain-error.log;
    #error_log off;


    ## REWRITES BELOW ##
    
    ## INCLUDE COMMONS ##

    include php.conf;
    include errors.conf;
    include drop.conf;
    include expires.conf;
}
EOF

# Creating {public,log} directories
#mkdir -p $WEB_DIR/$username/{public_html,logs}

# Creating index.html file
cat > $DOMAIN_DIR/index.html <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
      	<title>$domain</title>
        <meta charset="utf-8" />
</head>
<body class="container">
        <header><h1>$domain<h1></header>
        <div id="wrapper"><p>Hello World</p></div>
        <footer>© $(date +%Y)</footer>
</body>
</html>
EOF

# Changing permissions
chown -R $WEB_USER:$WEB_USER $WEB_DIR/$username
service nginx restart
ok "Site Created for $domain"


