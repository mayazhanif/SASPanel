#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
sudo apt-get install -y mysql-server nginx curl wget acl
apt-get install nginx vsftpd
cat > /etc/nginx/php.conf <<EOF
	location ~ \.php$ {
		include snippets/fastcgi-php.conf;
		fastcgi_pass unix:/var/run/php/php-fpm.sock;
	}
EOF
cat > /etc/nginx/sites-available/default <<EOF
server {
	listen 80 default_server;
	listen [::]:80 default_server;
	root /var/www/html;
	index index.php index.html index.htm index.nginx-debian.html;
	server_name _;
	location / {
		try_files \$uri \$uri/ =404;
	}
	include php.conf;
	include snippets/phpmyadmin.conf;
}
EOF
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
