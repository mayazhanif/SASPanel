#!/bin/bash
# installer.sh — SASPanel base system setup
# R16-09 FIX: added set -euo pipefail (consistent with all other scripts)
# Script is invoked as root by install_packages() so sudo is not needed.
set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
apt-get install -y mysql-server nginx curl wget acl
echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
echo "postfix postfix/mailname string mail.saspanel.org" | debconf-set-selections
mkdir -p /etc/nginx/backupDomains

cat > /etc/nginx/php.conf <<EOF
	location ~ \.php$ {
		include snippets/fastcgi-php.conf;
		fastcgi_pass unix:/var/run/php/php-fpm.sock;
	}
EOF
cat > /etc/nginx/sites-available/default <<EOF
server {
	listen 80 default_server;
	root /var/www/html;
	index index.php index.html index.htm index.nginx-debian.html;
	server_name _;
	location / {
		try_files \$uri \$uri/ =404;
	}
	include php.conf;
	include snippets/phpmyadmin.conf;
	include snippets/roundcube.conf;
    include snippets/webftp.conf;
}
EOF
sed -i 's/# server_names_hash_bucket_size 64/server_names_hash_bucket_size 64/' /etc/nginx/nginx.conf
service nginx restart
cat > /etc/vsftpd.conf <<EOF
listen=YES
local_enable=YES
write_enable=YES
local_umask=022
dirmessage_enable=YES
use_localtime=YES
xferlog_enable=YES
secure_chroot_dir=/var/run/vsftpd/empty
pam_service_name=vsftpd
rsa_cert_file=/etc/ssl/private/vsftpd.pem
chroot_local_user=YES
seccomp_sandbox=NO
isolate_network=NO
allow_writeable_chroot=YES
EOF
service vsftpd restart
