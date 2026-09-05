#!/bin/bash
# add_vhost.sh — Create Nginx virtual host for a domain
# SH-04 FIX: All variables are now quoted to prevent word splitting and glob injection

set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

# SH-04: Validate args (belt-and-suspenders — Python already validates these)
username="${1:?Username argument is required}"
domain="${2:?Domain argument is required}"

# Reject values containing path traversal or shell metacharacters
if [[ "$username" =~ [^a-z0-9_-] ]]; then
    echo "ERROR: Invalid username '${username}'" >&2; exit 1
fi
if [[ "$domain" =~ [^a-zA-Z0-9.\-] ]]; then
    echo "ERROR: Invalid domain '${domain}'" >&2; exit 1
fi

# Variables
NGINX_AVAILABLE_VHOSTS='/etc/nginx/sites-available'
NGINX_ENABLED_VHOSTS='/etc/nginx/sites-enabled'
WEB_DIR='/home'
WEB_USER="${username}"

# SH-04 FIX: all mkdir/chown/chmod use quoted variables
mkdir -p "${WEB_DIR}/${WEB_USER}/logs"
mkdir -p "${WEB_DIR}/${WEB_USER}/domains/${domain}/public_html"
mkdir -p "${WEB_DIR}/${WEB_USER}/crobjobs/logs"
chown -R "${WEB_USER}:${WEB_USER}" "${WEB_DIR}/${WEB_USER}/"

# Root check
[ "$(id -g)" != "0" ] && echo "Script must be run as root." >&2 && exit 1

# Create nginx vhost config (domain is whitelist-validated above)
cat > "${NGINX_AVAILABLE_VHOSTS}/${domain}-vhost.conf" <<EOF
server {
    listen   80;
    server_name ${domain} www.${domain};
    root  ${WEB_DIR}/${WEB_USER}/domains/${domain}/public_html;
    charset  utf-8;
    index index.php index.html index.htm;

    access_log ${WEB_DIR}/${WEB_USER}/logs/${domain}-access.log;
    error_log  ${WEB_DIR}/${WEB_USER}/logs/${domain}-error.log;

    include php.conf;
    include snippets/phpmyadmin.conf;
}
EOF

# Create placeholder index.html
cat > "${WEB_DIR}/${WEB_USER}/domains/${domain}/public_html/index.html" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <title>${domain}</title>
    <meta charset="utf-8" />
</head>
<body>
    <header><h1>${domain}</h1></header>
    <div id="wrapper"><p>Hello World</p></div>
    <footer>&copy; $(date +%Y)</footer>
</body>
</html>
EOF

# Permissions — all variables quoted
chown -R "${WEB_USER}:${WEB_USER}" "${WEB_DIR}/${WEB_USER}"
ln -sf "${NGINX_AVAILABLE_VHOSTS}/${domain}-vhost.conf" \
       "${NGINX_ENABLED_VHOSTS}/${domain}-vhost.conf"

service nginx restart
echo "Site created for ${domain}"
