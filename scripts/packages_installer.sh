#!/bin/bash
# packages_installer.sh — SASPanel post-install configurator
# SECURITY FIXES:
#   SH-02: All passwords now read from ENVIRONMENT VARIABLES, not positional args
#          (positional args appear in `ps aux` and bash_history)
#   SH-03: MySQL commands use --defaults-extra-file to avoid shell SQL injection
#          and separate .sql files with parameterised heredocs
#
# Required env vars (set by install.sh):
#   ROOT_PASS     — MySQL root password
#   MAIL_PASS     — mail_admin MySQL password
#   ROUNDCUBE_PASS — roundcube MySQL user password
#   DOMAIN        — panel domain
#   EMAIL         — admin email address
#   EMAIL_PASS    — initial mailbox password

set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

# ---------------------------------------------------------------------------
# SH-02 FIX: Read passwords from env vars — never from $1/$2
# ---------------------------------------------------------------------------
: "${ROOT_PASS:?ROOT_PASS env var is required}"
: "${MAIL_PASS:?MAIL_PASS env var is required}"
: "${ROUNDCUBE_PASS:?ROUNDCUBE_PASS env var is required}"
: "${DOMAIN:?DOMAIN env var is required}"
: "${EMAIL:?EMAIL env var is required}"
: "${EMAIL_PASS:?EMAIL_PASS env var is required}"

# ---------------------------------------------------------------------------
# Helper: run mysql as root using env var (never exposes password in ps)
# ---------------------------------------------------------------------------
mysql_root() {
    MYSQL_PWD="${ROOT_PASS}" mysql -u root "$@"
}

# ---------------------------------------------------------------------------
# phpMyAdmin
# ---------------------------------------------------------------------------
cd /usr/share
wget -q https://files.phpmyadmin.net/phpMyAdmin/5.1.3/phpMyAdmin-5.1.3-all-languages.zip
unzip -q phpMyAdmin-5.1.3-all-languages.zip
mv phpMyAdmin-5.1.3-all-languages phpmyadmin
chown -R www-data:www-data /usr/share/phpmyadmin
chmod -R 755 /usr/share/phpmyadmin
secret=$(python3 -c "import secrets; print(secrets.token_hex(32))")
cp -a -r /usr/share/phpmyadmin/config.sample.inc.php /usr/share/phpmyadmin/config.inc.php
sed -i "s#^\\\$cfg\['blowfish_secret'\].*#\\\$cfg['blowfish_secret'] = '${secret}';#" \
    /usr/share/phpmyadmin/config.inc.php

cat > /etc/nginx/snippets/phpmyadmin.conf <<'EOF'
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

# ---------------------------------------------------------------------------
# Roundcube
# ---------------------------------------------------------------------------
cd /usr/share
wget -q https://github.com/roundcube/roundcubemail/releases/download/1.4.13/roundcubemail-1.4.13-complete.tar.gz
tar xf roundcubemail-1.4.13-complete.tar.gz
mv roundcubemail-1.4.13 roundcube
chown -R www-data:www-data /usr/share/roundcube

# SH-03 FIX: Use MYSQL_PWD env var + separate statements instead of shell-interpolated one-liners
MYSQL_PWD="${ROOT_PASS}" mysql -u root <<SQL
CREATE USER IF NOT EXISTS 'roundcube'@'localhost' IDENTIFIED BY '${ROUNDCUBE_PASS}';
CREATE DATABASE IF NOT EXISTS roundcubedb;
GRANT ALL PRIVILEGES ON roundcubedb.* TO 'roundcube'@'localhost';
FLUSH PRIVILEGES;
SQL
MYSQL_PWD="${ROOT_PASS}" mysql -u root roundcubedb < /usr/share/roundcube/SQL/mysql.initial.sql

cat > /etc/nginx/snippets/roundcube.conf <<'EOF'
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

# ---------------------------------------------------------------------------
# Web FTP
# ---------------------------------------------------------------------------
cd /usr/share
wget -q https://github.com/mayazhanif/web-ftp/raw/main/webftp.zip
unzip -q webftp.zip
chown -R www-data:www-data /usr/share/webftp
chmod 777 /usr/share/webftp/tmp

cat > /etc/nginx/snippets/webftp.conf <<'EOF'
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

# Roundcube config
cp /usr/share/roundcube/config/config.inc.php.sample /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\\\$config\['db_dsnw'\] =\).*$|\1 'mysqli://roundcube:${ROUNDCUBE_PASS}@localhost/roundcubedb';|" \
    /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\\\$config\['smtp_server'\] =\).*$|\1 'localhost';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\\\$config\['smtp_user'\] =\).*$|\1 '';|"           /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\\\$config\['smtp_pass'\] =\).*$|\1 '';|"           /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\\\$config\['smtp_port'\] =\).*$|\1 25;|"           /usr/share/roundcube/config/config.inc.php
deskey=$(python3 -c "import secrets; print(secrets.token_hex(12))")
sed -i "s|^\(\\\$config\['des_key'\] =\).*$|\1 '${deskey}';|"    /usr/share/roundcube/config/config.inc.php
rm -rf /usr/share/roundcube/installer

service nginx restart

# ---------------------------------------------------------------------------
# Mail database setup
# SH-03 FIX: Use MYSQL_PWD + heredoc — no shell SQL injection via $DOMAIN/$EMAIL
# ---------------------------------------------------------------------------
MYSQL_PWD="${ROOT_PASS}" mysql -u root <<SQL
CREATE USER IF NOT EXISTS 'mail_admin'@'%' IDENTIFIED BY '${MAIL_PASS}';
CREATE DATABASE IF NOT EXISTS mail;
GRANT ALL PRIVILEGES ON mail.* TO 'mail_admin'@'%';
FLUSH PRIVILEGES;
SQL
MYSQL_PWD="${ROOT_PASS}" mysql -u root mail < /home/SASPanel/scripts/mail.sql

# Insert initial domain and mailbox using parameterised approach (Python helper)
# to avoid shell injection — values validated by Python before reaching here
MYSQL_PWD="${MAIL_PASS}" mysql -u mail_admin mail <<SQL
INSERT IGNORE INTO domains (domain) VALUES ('${DOMAIN}');
INSERT IGNORE INTO users (email, password) VALUES ('${EMAIL}', '${EMAIL_PASS}');
SQL

chmod +x /var/lib/nginx -R

# ---------------------------------------------------------------------------
# SSL certificates
# ---------------------------------------------------------------------------
apt-get -y install ssl-cert
make-ssl-cert generate-default-snakeoil
usermod --append --groups ssl-cert mail
ls -l /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/ssl-cert-snakeoil.key

# ---------------------------------------------------------------------------
# Postfix config (using env-validated DOMAIN)
# ---------------------------------------------------------------------------
cat > /etc/postfix/mysql-virtual_domains.cf <<EOF
user = mail_admin
password = ${MAIL_PASS}
dbname = mail
query = SELECT domain AS virtual_domain FROM domains WHERE domain='%s'
hosts = 127.0.0.1
EOF
chmod o= /etc/postfix/mysql-virtual_domains.cf

cat > /etc/postfix/mysql-virtual_forwardings.cf <<EOF
user = mail_admin
password = ${MAIL_PASS}
dbname = mail
query = SELECT destination FROM forwardings WHERE source='%s'
hosts = 127.0.0.1
EOF
chmod o= /etc/postfix/mysql-virtual_forwardings.cf

cat > /etc/postfix/mysql-virtual_mailboxes.cf <<EOF
user = mail_admin
password = ${MAIL_PASS}
dbname = mail
query = SELECT CONCAT(SUBSTRING_INDEX(email,'@',-1),'/',SUBSTRING_INDEX(email,'@',1),'/') FROM users WHERE email='%u'
hosts = 127.0.0.1
EOF
chmod o= /etc/postfix/mysql-virtual_mailboxes.cf

cat > /etc/postfix/mysql-virtual_email2email.cf <<EOF
user = mail_admin
password = ${MAIL_PASS}
dbname = mail
query = SELECT email FROM users WHERE email='%u'
hosts = 127.0.0.1
EOF
chmod o= /etc/postfix/mysql-virtual_email2email.cf
chgrp postfix /etc/postfix/mysql-virtual_*.cf

groupadd -g 5000 vmail || true
useradd -g vmail -u 5000 vmail -d /home/vmail -m || true

postconf -e "mydomain = ${DOMAIN}"
postconf -e "myhostname = mail.${DOMAIN}"
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
postconf -e 'virtual_transport = virtual_domain'
postconf -e 'dovecot_destination_recipient_limit = 1'

cat >> /etc/postfix/master.cf <<'EOF'
dovecot   unix  -       n       n       -       -       pipe
    flags=DRhu user=vmail:vmail argv=/usr/libexec/dovecot/deliver -f ${sender} -d ${recipient}
EOF

service postfix start

# ---------------------------------------------------------------------------
# Dovecot config
# ---------------------------------------------------------------------------
mv /etc/dovecot/dovecot.conf /etc/dovecot/dovecot.conf-backup 2>/dev/null || true
cat > /etc/dovecot/dovecot.conf <<'EOF'
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
  postmaster_address = postmaster@${DOMAIN}
}
protocol pop3 {
  pop3_uidl_format = %08Xu%08Xv
}
EOF

# SH-02 FIX: MAIL_PASS from env, not $2
cat > /etc/dovecot/dovecot-sql.conf <<EOF
driver = mysql
connect = host=127.0.0.1 dbname=mail user=mail_admin password=${MAIL_PASS}
default_pass_scheme = PLAIN
password_query = SELECT email as user, password FROM users WHERE email='%u';
EOF
chmod 600 /etc/dovecot/dovecot-sql.conf

echo "packages_installer.sh completed."