#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd /usr/share
rootpwd=$1
pwd=$2
domain=$3
emailaddress=$4
emailpassword=$5
wget https://files.phpmyadmin.net/phpMyAdmin/5.1.3/phpMyAdmin-5.1.3-all-languages.zip
unzip phpMyAdmin-5.1.3-all-languages.zip
mv phpMyAdmin-5.1.3-all-languages phpmyadmin
chown -R www-data:www-data /usr/share/phpmyadmin
chmod -R 755 /usr/share/phpmyadmin
secret=`cat /dev/urandom | head -n 32 | md5sum | head -c 32`;
\cp -a -r /usr/share/phpmyadmin/config.sample.inc.php  /usr/share/phpmyadmin/config.inc.php
sed -i "s#^\$cfg\['blowfish_secret'\].*#\$cfg\['blowfish_secret'\] = '${secret}';#" /usr/share/phpmyadmin/config.inc.php
sed -i "s#^\$cfg\['blowfish_secret'\].*#\$cfg\['blowfish_secret'\] = '${secret}';#" /usr/share/phpmyadmin//libraries/config.default.php
#sed -i "s#^\$i]['host'\].*#\$i]['host'\] = '127.0.0.1';#" /usr/share/phpmyadmin/config.inc.php
#sed -i "s#^\$i]['host'\].*#\$i]['host'\] = '127.0.0.1';#" /usr/share/phpmyadmin//libraries/config.default.php

cat > /etc/nginx/snippets/phpmyadmin.conf <<EOF
location /phpmyadmin {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/phpmyadmin/(.+\.php)$ {
        root /usr/share/;
		include php.conf;
    }
    location ~* ^/phpmyadmin/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF


cd /usr/share
wget https://github.com/roundcube/roundcubemail/releases/download/1.4.13/roundcubemail-1.4.13-complete.tar.gz
tar xvf roundcubemail-1.4.13-complete.tar.gz
mv roundcubemail-1.4.13 roundcube
chown -R www-data:www-data /usr/share/roundcube
mysql -u root -p${rootpwd} -e "CREATE USER 'roundcube'@'localhost' IDENTIFIED BY '${rootpwd}';FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} -e "create database roundcubedb;FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} -e "GRANT ALL PRIVILEGES ON roundcubedb.* TO 'roundcube'@'localhost';FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} roundcubedb < /usr/share/roundcube/SQL/mysql.initial.sql
cat > /etc/nginx/snippets/roundcube.conf <<EOF
location /roundcube {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/roundcube/(.+\.php)$ {
        root /usr/share/;
		include php.conf;
    }
    location ~* ^/roundcube/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF
#cp /usr/share/roundcube/config/config.inc.php.sample /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['db_dsnw'\] =\).*$|\1 \'mysqli://roundcube:${pwd}@localhost/roundcubedb\';|" /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['smtp_server'\] =\).*$|\1 \'localhost\';|" /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['smtp_user'\] =\).*$|\1 \'%u\';|" /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['smtp_pass'\] =\).*$|\1 \'%p\';|" /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['support_url'\] =\).*$|\1 \'mailto:${E}\';|" /var/www/html/roundcube/config/config.inc.php
#deskey=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9-_#&!*%?' | fold -w 24 | head -n 1)
#sed -i "s|^\(\$config\['des_key'\] =\).*$|\1 \'${deskey}\';|" /usr/share/roundcube/config/config.inc.php
#rm -rf /usr/share/roundcube/installer

cd /usr/share
wget https://github.com/mayazhanif/web-ftp/raw/main/webftp.zip
unzip webftp.zip
chown -R www-data:www-data /usr/share/webftp
chmod 777 /usr/share/webftp/tmp
cat > /etc/nginx/snippets/webftp.conf <<EOF
location /webftp {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/webftp/(.+\.php)$ {
        root /usr/share/;
		include php.conf;
    }
    location ~* ^/webftp/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF
service nginx restart
cp /usr/share/roundcube/config/config.inc.php.sample /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['db_dsnw'\] =\).*$|\1 \'mysqli://roundcube:${rootpwd}@localhost/roundcubedb\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_server'\] =\).*$|\1 \'localhost\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_user'\] =\).*$|\1 \'\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_pass'\] =\).*$|\1 \'\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_port'\] =\).*$|\1 25;|" /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['support_url'\] =\).*$|\1 \'mailto:${E}\';|" /var/www/html/roundcube/config/config.inc.php
#deskey=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9-_#&!*%?' | fold -w 24 | head -n 1)
#deskey=$(cat /dev/urandom | tr -dc '[:alpha:]' | fold -w ${1:-24} | head -n 1)
deskey=$(xxd -l 12 -c 12 -p < /dev/random)
sed -i "s|^\(\$config\['des_key'\] =\).*$|\1 \'${deskey}\';|" /usr/share/roundcube/config/config.inc.php
rm -rf /usr/share/roundcube/installer
#echo -e "\n\$cfg['Servers'][\$i]['auth_type'] = 'signon';\n\$cfg['Servers'][\$i]['SignonSession'] = 'SignonSession';\n\$cfg['Servers'][\$i]['SignonURL'] = 'sso.php';\n" >> /usr/share/phpmyadmin/config.inc.php
service nginx restart

mysql -u root -p${rootpwd} -e "CREATE USER 'mail_admin'@'%' IDENTIFIED BY '${pwd}';FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} -e "create database mail;use mail;FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} -e "GRANT ALL PRIVILEGES ON mail.* TO 'mail_admin'@'%';FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} -e "use mail;GRANT ALL PRIVILEGES ON mail.* TO 'mail_admin'@'%'; ALTER USER 'mail_admin'@'%';FLUSH PRIVILEGES;"
mysql -u root -p${rootpwd} -e "use mail;INSERT INTO domains VALUES ('${domain}');INSERT INTO users VALUES ('${emailaddress}','${emailpassword}')"
mysql -u root -p${rootpwd} mail < /home/SASPanel/scripts/mail.sql
chmod +x /var/lib/nginx -R
sudo apt-get -y install ssl-cert
sudo make-ssl-cert generate-default-snakeoil
sudo usermod --append --groups ssl-cert mail
ls -l /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/ssl-cert-snakeoil.key

cat > /etc/postfix/mysql-virtual_domains.cf << EOF
user = mail_admin
password = ${pwd}
dbname = mail
query = SELECT domain AS virtual_domain FROM domains WHERE domain='%s'
hosts = 127.0.0.1
EOF
cat > /etc/postfix/mysql-virtual_forwardings.cf << EOF
user = mail_admin
password = ${pwd}
dbname = mail
query = SELECT destination FROM forwardings WHERE source='%s'
hosts = 127.0.0.1
EOF
cat > /etc/postfix/mysql-virtual_mailboxes.cf << EOF
user = mail_admin
password = ${pwd}
dbname = mail
query = SELECT CONCAT(SUBSTRING_INDEX(email,'@',-1),'/',SUBSTRING_INDEX(email,'@',1),'/') FROM users WHERE email='%s'
hosts = 127.0.0.1
EOF
cat > /etc/postfix/mysql-virtual_email2email.cf << EOF
user = mail_admin
password = ${pwd}
dbname = mail
query = SELECT email FROM users WHERE email='%s'
hosts = 127.0.0.1
EOF
chmod o= /etc/postfix/mysql-virtual_*.cf
chgrp postfix /etc/postfix/mysql-virtual_*.cf
groupadd -g 5000 vmail
useradd -g vmail -u 5000 vmail -d /home/vmail -m

postconf -e 'myhostname = mail.saspanel.org'
postconf -e 'mydestination = localhost'
postconf -e 'mynetworks = 127.0.0.0/8'
postconf -e 'inet_interfaces = all'
postconf -e 'message_size_limit = 30720000'
postconf -e 'virtual_alias_domains ='
postconf -e 'virtual_alias_maps = proxy:mysql:/etc/postfix/mysql-virtual_forwardings.cf, mysql:/etc/postfix/mysql-virtual_email2email.cf'
postconf -e 'virtual_mailbox_domains = proxy:mysql:/etc/postfix/mysql-virtual_domains.cf'
postconf -e 'virtual_mailbox_maps = proxy:mysql:/etc/postfix/mysql-virtual_mailboxes.cf'
postconf -e 'virtual_mailbox_base = /home/vmail'
postconf -e 'virtual_uid_maps = static:5000'
postconf -e 'virtual_gid_maps = static:5000'
postconf -e 'smtpd_sasl_type = dovecot'
postconf -e 'smtpd_sasl_path = private/auth'
postconf -e 'smtpd_sasl_auth_enable = yes'
postconf -e 'broken_sasl_auth_clients = yes'
postconf -e 'smtpd_sasl_authenticated_header = yes'
postconf -e 'smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination'
postconf -e 'smtpd_use_tls = yes'
postconf -e 'smtpd_tls_cert_file = /etc/pki/dovecot/certs/dovecot.pem'
postconf -e 'smtpd_tls_key_file = /etc/pki/dovecot/private/dovecot.pem'
postconf -e 'virtual_create_maildirsize = yes'
postconf -e 'virtual_maildir_extended = yes'
postconf -e 'proxy_read_maps = $local_recipient_maps $mydestination $virtual_alias_maps $virtual_alias_domains $virtual_mailbox_maps $virtual_mailbox_domains $relay_recipient_maps $relay_domains $canonical_maps $sender_canonical_maps $recipient_canonical_maps $relocated_maps $transport_maps $mynetworks $virtual_mailbox_limit_maps'
postconf -e 'virtual_transport = virtual_domain'
postconf -e 'dovecot_destination_recipient_limit = 1'
# postfix master.conf configuration
echo "
dovecot   unix  -       n       n       -       -       pipe
    flags=DRhu user=vmail:vmail argv=/usr/libexec/dovecot/deliver -f ${sender} -d ${recipient}
" >> /etc/postfix/master.cf
# start postfix
service sendmail stop
#chkconfig sendmail off
#chkconfig postfix on
service postfix start
# backup dovecot.conf
mv /etc/dovecot/dovecot.conf /etc/dovecot/dovecot.conf-backup
# generate dovecot.conf
cat > /etc/dovecot/dovecot.conf << EOF
listen = *
protocols = imap pop3
log_timestamp = "%Y-%m-%d %H:%M:%S "
mail_location = maildir:/home/vmail/%d/%n
maildir_stat_dirs = yes
mail_privileged_group = postfix
namespace {
  type = private
  separator = .
  prefix = INBOX.
  inbox = yes
}
passdb {
  args = /etc/dovecot/dovecot-sql.conf
  driver = sql
}
service auth {
  unix_listener /var/spool/postfix/private/auth {
    group = postfix
    mode = 0660
    user = postfix
  }
  unix_listener auth-master {
    mode = 0600
    user = vmail
  }
  user = root
}
ssl_cert = </etc/dovecot/private/dovecot.pem
ssl_key = </etc/dovecot/private/dovecot.key
userdb {
  args = uid=5000 gid=5000 home=/home/vmail/%d/%n allow_all_users=yes
  driver = static
}
protocol lda {
  auth_socket_path = /var/run/dovecot/auth-master
  log_path = /home/vmail/dovecot-deliver.log
  postmaster_address = postmaster@saspanel.org
}
protocol pop3 {
  pop3_uidl_format = %08Xu%08Xv
}
EOF
# generate dovecot-sql.conf
cat > /etc/dovecot/dovecot-sql.conf << EOF
driver = mysql
connect = host=127.0.0.1 dbname=mail user=mail_admin password=${pwd}
default_pass_scheme = PLAIN
password_query = SELECT email as user, password FROM users WHERE email='%u';
EOF
# apply permissions
chgrp dovecot /etc/dovecot/dovecot-sql.conf
chmod o= /etc/dovecot/dovecot-sql.conf
# start dovecot
#chkconfig dovecot on
service dovecot restart
systemctl restart postfix
systemctl restart dovecot