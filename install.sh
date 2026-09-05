#!/usr/bin/env bash
# =============================================================================
#  SASPanel — Automated Installer
#  Version: 2.0 (Security-Hardened)
#
#  Usage:  sudo bash install.sh
#
#  What this script does:
#    1. Checks prerequisites (OS, root, internet)
#    2. Generates all passwords automatically (cryptographically secure)
#    3. Installs: MySQL, Nginx, PHP-FPM, Certbot, VSFTPD, Postfix, Dovecot
#    4. Configures: virtual mail stack, roundcube, webftp, phpmyadmin
#    5. Clones / updates SASPanel from /home/SASPanel
#    6. Sets up Python venv + pip dependencies
#    7. Writes Database/config.ini with generated credentials
#    8. Creates and enables saspanel.service (Gunicorn, starts on boot)
#    9. Saves all generated credentials to /root/saspanel_credentials.txt
#       (chmod 600) and reminds the admin to delete after saving.
#
#  Supported OS: Ubuntu 20.04 / 22.04 LTS
# =============================================================================

set -euo pipefail

# ── Colour helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
section() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}"; }

# ── Paths ──────────────────────────────────────────────────────────────────────
SASPANEL_DIR="/home/SASPanel"
CRED_FILE="/root/saspanel_credentials.txt"
LOG_FILE="/var/log/saspanel_install.log"
VENV_DIR="${SASPANEL_DIR}/venv"
SERVICE_NAME="saspanel"
SCRIPTS_DIR="${SASPANEL_DIR}/scripts"

# ── Redirect all output to log (and keep terminal output) ─────────────────────
exec > >(tee -a "$LOG_FILE") 2>&1

# =============================================================================
# 1. PRE-FLIGHT CHECKS
# =============================================================================
section "Pre-flight checks"

[[ "$(id -u)" -ne 0 ]] && error "This script must be run as root. Use: sudo bash install.sh"

# OS check
if ! grep -qiE 'ubuntu' /etc/os-release 2>/dev/null; then
    warn "This script is tested on Ubuntu 20.04/22.04. Proceeding anyway..."
fi

# Internet connectivity
if ! curl -s --max-time 5 https://api.ipify.org &>/dev/null; then
    error "No internet connection detected. Please check your network."
fi

# Detect server IP / ask for domain
SERVER_IP=$(curl -s --max-time 5 https://api.ipify.org || hostname -I | awk '{print $1}')
info "Server public IP: ${SERVER_IP}"

# Ask for domain (the only thing we need from the operator)
echo ""
echo -e "${BOLD}Enter your panel domain (e.g. panel.yourdomain.com):${NC}"
echo -e "${YELLOW}This domain must already point to this server's IP (${SERVER_IP}).${NC}"
read -r -p "Domain: " DOMAIN
[[ -z "$DOMAIN" ]] && error "Domain cannot be empty."

echo ""
echo -e "${BOLD}Enter the admin email address for Let's Encrypt notifications:${NC}"
read -r -p "Email: " ADMIN_EMAIL
[[ -z "$ADMIN_EMAIL" ]] && error "Email cannot be empty."

success "Domain: ${DOMAIN}  |  Email: ${ADMIN_EMAIL}"

# =============================================================================
# 2. GENERATE ALL CREDENTIALS SECURELY
# =============================================================================
section "Generating secure credentials"

# Cryptographically secure random passwords
gen_pass() { python3 -c "import secrets,string; \
    a=string.ascii_letters+string.digits+'!@#%^&*'; \
    print(''.join(secrets.choice(a) for _ in range(${1:-20})))"; }

gen_hex()  { python3 -c "import secrets; print(secrets.token_hex(${1:-16}))"; }

DB_ROOT_PASS=$(gen_pass 24)
DB_MAIL_PASS=$(gen_pass 24)
MAIL_ADMIN_EMAIL="${ADMIN_EMAIL}"
MAIL_ADMIN_PASS=$(gen_pass 20)
ROUNDCUBE_PASS=$(gen_pass 20)
PANEL_SECRET_KEY=$(gen_hex 32)

info "All credentials generated."

# =============================================================================
# 3. SAVE CREDENTIALS (before we do anything that could fail)
# =============================================================================
section "Saving credentials to ${CRED_FILE}"

cat > "${CRED_FILE}" <<EOF
# ============================================================
#  SASPanel Installation Credentials
#  Generated: $(date)
#  Server IP: ${SERVER_IP}
#  Domain: ${DOMAIN}
#
#  ⚠  DELETE THIS FILE after you have saved these credentials
#     somewhere safe (e.g. a password manager).
#     Command:  shred -u ${CRED_FILE}
# ============================================================

[Panel]
Domain            = ${DOMAIN}
Panel URL         = https://${DOMAIN}:5000
Admin Email       = ${ADMIN_EMAIL}

[Flask]
SECRET_KEY        = ${PANEL_SECRET_KEY}

[MySQL Root]
Host              = localhost
User              = root
Password          = ${DB_ROOT_PASS}
Database          = saspanel

[MySQL Mail Admin]
User              = mail_admin
Password          = ${DB_MAIL_PASS}
Database          = mail

[Default Mail Account]
Email             = ${MAIL_ADMIN_EMAIL}
Password          = ${MAIL_ADMIN_PASS}

[Roundcube DB]
User              = roundcube
Password          = ${ROUNDCUBE_PASS}
Database          = roundcubedb
EOF

chmod 600 "${CRED_FILE}"
success "Credentials saved to ${CRED_FILE} (chmod 600)"

# =============================================================================
# 4. SYSTEM UPDATE
# =============================================================================
section "Updating system packages"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y \
    curl wget git acl unzip python3 python3-pip python3-venv \
    software-properties-common gnupg lsb-release xxd

success "System updated."

# =============================================================================
# 5. INSTALL NGINX
# =============================================================================
section "Installing Nginx"

apt-get install -y nginx
mkdir -p /etc/nginx/backupDomains
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled
mkdir -p /etc/nginx/snippets

# Default vhost — serves phpmyadmin, roundcube, webftp
cat > /etc/nginx/sites-available/default <<'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    root /var/www/html;
    index index.php index.html index.htm;
    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }
    include /etc/nginx/php.conf;
    include snippets/phpmyadmin.conf;
    include snippets/roundcube.conf;
    include snippets/webftp.conf;
}
NGINXEOF

ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Shared PHP-FPM location block
cat > /etc/nginx/php.conf <<'PHPEOF'
location ~ \.php$ {
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:/var/run/php/php-fpm.sock;
}
PHPEOF

sed -i 's/# server_names_hash_bucket_size 64/server_names_hash_bucket_size 64/' /etc/nginx/nginx.conf
systemctl enable nginx
systemctl restart nginx
success "Nginx installed and configured."

# =============================================================================
# 6. INSTALL PHP
# =============================================================================
section "Installing PHP"

apt-get install -y \
    php-common php-cli php-fpm \
    php-mysql php-net-ldap2 php-net-ldap3 php-imagick \
    php-gd php-imap php-json php-curl php-zip php-xml \
    php-mbstring php-bz2 php-intl php-gmp \
    php-net-smtp php-mail-mime php-net-idna2 mailutils

# Find the PHP-FPM sock and update the nginx conf if needed
PHP_FPM_SOCK=$(find /var/run/php/ -name "php*-fpm.sock" 2>/dev/null | head -1)
if [[ -n "$PHP_FPM_SOCK" ]]; then
    sed -i "s|unix:/var/run/php/php-fpm.sock|unix:${PHP_FPM_SOCK}|g" /etc/nginx/php.conf
fi

systemctl enable php*-fpm || true
systemctl restart php*-fpm || true
success "PHP installed."

# =============================================================================
# 7. INSTALL MYSQL
# =============================================================================
section "Installing MySQL"

apt-get install -y mysql-server

# Secure MySQL — set root password, remove anonymous users, disable remote root
mysql -u root <<MYSQLEOF
-- Root password
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';
-- Disable remote root login
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
-- Remove test database
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
-- Create saspanel database and admin user
CREATE DATABASE IF NOT EXISTS saspanel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'saspanel_user'@'localhost' IDENTIFIED BY '${DB_ROOT_PASS}';
GRANT ALL PRIVILEGES ON saspanel.* TO 'saspanel_user'@'localhost';
FLUSH PRIVILEGES;
MYSQLEOF

# Import SASPanel schema
if [[ -f "${SCRIPTS_DIR}/database.sql" ]]; then
    mysql -u root -p"${DB_ROOT_PASS}" saspanel < "${SCRIPTS_DIR}/database.sql"
    success "SASPanel database schema imported."
else
    warn "scripts/database.sql not found — import manually after install."
fi

systemctl enable mysql
systemctl restart mysql
success "MySQL installed and secured."

# =============================================================================
# 8. INSTALL CERTBOT
# =============================================================================
section "Installing Certbot"

apt-get install -y certbot python3-certbot-nginx
success "Certbot installed."

# =============================================================================
# 9. INSTALL VSFTPD (FTP)
# =============================================================================
section "Installing VSFTPD"

apt-get install -y vsftpd

# Create chroot list
touch /etc/vsftpd.chroot_list

cat > /etc/vsftpd.conf <<'FTPEOF'
listen=YES
listen_ipv6=NO
local_enable=YES
write_enable=YES
local_umask=022
dirmessage_enable=YES
use_localtime=YES
xferlog_enable=YES
secure_chroot_dir=/var/run/vsftpd/empty
pam_service_name=vsftpd
rsa_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
rsa_private_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
ssl_enable=NO
chroot_local_user=YES
chroot_list_enable=YES
chroot_list_file=/etc/vsftpd.chroot_list
allow_writeable_chroot=YES
userlist_enable=YES
userlist_file=/etc/vsftpd.user_list
userlist_deny=NO
FTPEOF

touch /etc/vsftpd.user_list
systemctl enable vsftpd
systemctl restart vsftpd
success "VSFTPD installed."

# =============================================================================
# 10. INSTALL POSTFIX + DOVECOT (Mail Stack)
# =============================================================================
section "Installing Postfix + Dovecot"

# Pre-seed debconf to avoid interactive prompts
echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
echo "postfix postfix/mailname string mail.${DOMAIN}"          | debconf-set-selections
echo "dovecot-core dovecot-core/create-ssl-cert boolean true"  | debconf-set-selections

apt-get install -y \
    postfix postfix-mysql \
    dovecot-core dovecot-imapd dovecot-pop3d dovecot-lmtpd dovecot-mysql \
    ssl-cert

# Mail database
mysql -u root -p"${DB_ROOT_PASS}" <<MAILDBEOF
CREATE DATABASE IF NOT EXISTS mail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'mail_admin'@'localhost' IDENTIFIED BY '${DB_MAIL_PASS}';
GRANT ALL PRIVILEGES ON mail.* TO 'mail_admin'@'localhost';
FLUSH PRIVILEGES;
MAILDBEOF

if [[ -f "${SCRIPTS_DIR}/mail.sql" ]]; then
    mysql -u root -p"${DB_ROOT_PASS}" mail < "${SCRIPTS_DIR}/mail.sql"
    success "Mail schema imported."
fi

# Seed first domain and admin mail account
mysql -u root -p"${DB_ROOT_PASS}" mail <<MAILSEEDEOF
INSERT IGNORE INTO domains (domain) VALUES ('${DOMAIN}');
INSERT IGNORE INTO users (email, password) VALUES ('${MAIL_ADMIN_EMAIL}', '${MAIL_ADMIN_PASS}');
MAILSEEDEOF

# Virtual mail user
groupadd -g 5000 vmail 2>/dev/null || true
useradd -g vmail -u 5000 vmail -d /home/vmail -m 2>/dev/null || true
make-ssl-cert generate-default-snakeoil --force-overwrite
usermod --append --groups ssl-cert postfix 2>/dev/null || true

# Postfix MySQL connector files (passwords from variables, not shell args)
chmod o= /etc/postfix/
cat > /etc/postfix/mysql-virtual_domains.cf <<EOF
user = mail_admin
password = ${DB_MAIL_PASS}
dbname = mail
query = SELECT domain AS virtual_domain FROM domains WHERE domain='%s'
hosts = 127.0.0.1
EOF

cat > /etc/postfix/mysql-virtual_forwardings.cf <<EOF
user = mail_admin
password = ${DB_MAIL_PASS}
dbname = mail
query = SELECT destination FROM forwardings WHERE source='%s'
hosts = 127.0.0.1
EOF

cat > /etc/postfix/mysql-virtual_mailboxes.cf <<EOF
user = mail_admin
password = ${DB_MAIL_PASS}
dbname = mail
query = SELECT CONCAT(SUBSTRING_INDEX(email,'@',-1),'/',SUBSTRING_INDEX(email,'@',1),'/') FROM users WHERE email='%s'
hosts = 127.0.0.1
EOF

cat > /etc/postfix/mysql-virtual_email2email.cf <<EOF
user = mail_admin
password = ${DB_MAIL_PASS}
dbname = mail
query = SELECT email FROM users WHERE email='%s'
hosts = 127.0.0.1
EOF

chmod o= /etc/postfix/mysql-virtual_*.cf
chgrp postfix /etc/postfix/mysql-virtual_*.cf

# Postfix main config
postconf -e "myhostname = mail.${DOMAIN}"
postconf -e "mydomain = ${DOMAIN}"
postconf -e "mydestination = localhost"
postconf -e "mynetworks = 127.0.0.0/8"
postconf -e "inet_interfaces = all"
postconf -e "message_size_limit = 30720000"
postconf -e "virtual_alias_domains ="
postconf -e "virtual_alias_maps = proxy:mysql:/etc/postfix/mysql-virtual_forwardings.cf, mysql:/etc/postfix/mysql-virtual_email2email.cf"
postconf -e "virtual_mailbox_domains = proxy:mysql:/etc/postfix/mysql-virtual_domains.cf"
postconf -e "virtual_mailbox_maps = proxy:mysql:/etc/postfix/mysql-virtual_mailboxes.cf"
postconf -e "virtual_mailbox_base = /home/vmail"
postconf -e "virtual_uid_maps = static:5000"
postconf -e "virtual_gid_maps = static:5000"
postconf -e "smtpd_sasl_type = dovecot"
postconf -e "smtpd_sasl_path = private/auth"
postconf -e "smtpd_sasl_auth_enable = yes"
postconf -e "broken_sasl_auth_clients = yes"
postconf -e "smtpd_sasl_authenticated_header = yes"
postconf -e "smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination"
postconf -e "smtpd_use_tls = yes"
postconf -e "smtpd_tls_cert_file = /etc/ssl/certs/ssl-cert-snakeoil.pem"
postconf -e "smtpd_tls_key_file = /etc/ssl/private/ssl-cert-snakeoil.key"
postconf -e "virtual_create_maildirsize = yes"
postconf -e "virtual_maildir_extended = yes"

# Dovecot config
mv /etc/dovecot/dovecot.conf /etc/dovecot/dovecot.conf.bak 2>/dev/null || true

cat > /etc/dovecot/dovecot.conf <<'DOVEEOF'
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
ssl_cert = </etc/ssl/certs/ssl-cert-snakeoil.pem
ssl_key = </etc/ssl/private/ssl-cert-snakeoil.key
userdb {
  args = uid=5000 gid=5000 home=/home/vmail/%d/%n allow_all_users=yes
  driver = static
}
protocol lda {
  auth_socket_path = /var/run/dovecot/auth-master
  log_path = /home/vmail/dovecot-deliver.log
  postmaster_address = postmaster@PLACEHOLDER_DOMAIN
}
protocol pop3 {
  pop3_uidl_format = %08Xu%08Xv
}
DOVEEOF

# Replace placeholder with real domain
sed -i "s/PLACEHOLDER_DOMAIN/${DOMAIN}/" /etc/dovecot/dovecot.conf

cat > /etc/dovecot/dovecot-sql.conf <<EOF
driver = mysql
connect = host=127.0.0.1 dbname=mail user=mail_admin password=${DB_MAIL_PASS}
default_pass_scheme = PLAIN
password_query = SELECT email as user, password FROM users WHERE email='%u';
EOF
chmod 600 /etc/dovecot/dovecot-sql.conf

systemctl enable postfix dovecot
systemctl restart postfix dovecot
success "Postfix + Dovecot installed and configured."

# =============================================================================
# 11. INSTALL PHPMYADMIN
# =============================================================================
section "Installing phpMyAdmin"

DEBIAN_FRONTEND=noninteractive apt-get install -y phpmyadmin || true

cat > /etc/nginx/snippets/phpmyadmin.conf <<'EOF'
location /phpmyadmin {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/phpmyadmin/(.+\.php)$ {
        root /usr/share/;
        include /etc/nginx/php.conf;
    }
    location ~* ^/phpmyadmin/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF

success "phpMyAdmin configured."

# =============================================================================
# 12. INSTALL ROUNDCUBE WEBMAIL
# =============================================================================
section "Installing Roundcube"

cd /usr/share
if [[ ! -d roundcube ]]; then
    wget -q https://github.com/roundcube/roundcubemail/releases/download/1.6.6/roundcubemail-1.6.6-complete.tar.gz
    tar xf roundcubemail-1.6.6-complete.tar.gz
    mv roundcubemail-1.6.6 roundcube
    rm -f roundcubemail-1.6.6-complete.tar.gz
fi
chown -R www-data:www-data /usr/share/roundcube

mysql -u root -p"${DB_ROOT_PASS}" <<RCEOF
CREATE DATABASE IF NOT EXISTS roundcubedb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'roundcube'@'localhost' IDENTIFIED BY '${ROUNDCUBE_PASS}';
GRANT ALL PRIVILEGES ON roundcubedb.* TO 'roundcube'@'localhost';
FLUSH PRIVILEGES;
RCEOF

mysql -u root -p"${DB_ROOT_PASS}" roundcubedb < /usr/share/roundcube/SQL/mysql.initial.sql 2>/dev/null || true

cp /usr/share/roundcube/config/config.inc.php.sample /usr/share/roundcube/config/config.inc.php
DESKEY=$(xxd -l 12 -c 12 -p < /dev/urandom)
sed -i "s|^\(\$config\['db_dsnw'\] =\).*$|\1 'mysqli://roundcube:${ROUNDCUBE_PASS}@localhost/roundcubedb';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_server'\] =\).*$|\1 'localhost';|"  /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_port'\] =\).*$|\1 25;|"             /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['des_key'\] =\).*$|\1 '${DESKEY}';|"      /usr/share/roundcube/config/config.inc.php
rm -rf /usr/share/roundcube/installer

cat > /etc/nginx/snippets/roundcube.conf <<'EOF'
location /roundcube {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/roundcube/(.+\.php)$ {
        root /usr/share/;
        include /etc/nginx/php.conf;
    }
    location ~* ^/roundcube/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF

success "Roundcube installed."

# =============================================================================
# 13. INSTALL WEB-FTP
# =============================================================================
section "Installing Web-FTP"

cd /usr/share
if [[ ! -d webftp ]]; then
    wget -q https://github.com/mayazhanif/web-ftp/raw/main/webftp.zip
    unzip -q webftp.zip
    rm -f webftp.zip
fi
chown -R www-data:www-data /usr/share/webftp
chmod 777 /usr/share/webftp/tmp 2>/dev/null || true

cat > /etc/nginx/snippets/webftp.conf <<'EOF'
location /webftp {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/webftp/(.+\.php)$ {
        root /usr/share/;
        include /etc/nginx/php.conf;
    }
    location ~* ^/webftp/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF

systemctl restart nginx
success "Web-FTP installed."

# =============================================================================
# 14. SETUP SASPANEL PYTHON APP
# =============================================================================
section "Setting up SASPanel Python application"

# Ensure SASPanel directory exists
if [[ ! -d "${SASPANEL_DIR}" ]]; then
    error "SASPanel directory not found at ${SASPANEL_DIR}. Clone the repo first:\n  git clone https://github.com/mayazhanif/SASPanel.git ${SASPANEL_DIR}"
fi

cd "${SASPANEL_DIR}"

# Python virtual environment
if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
    success "Python venv created at ${VENV_DIR}"
fi

# Install dependencies
"${VENV_DIR}/bin/pip" install --upgrade pip -q
"${VENV_DIR}/bin/pip" install gunicorn -q

if [[ -f "${SASPANEL_DIR}/requirements.txt" ]]; then
    "${VENV_DIR}/bin/pip" install -r "${SASPANEL_DIR}/requirements.txt" -q
    success "Python dependencies installed."
fi

# Write config.ini from generated credentials
cat > "${SASPANEL_DIR}/Database/config.ini" <<EOF
[config]
host = localhost
user = root
password = ${DB_ROOT_PASS}
database = saspanel

[mail]
server = localhost
email = ${MAIL_ADMIN_EMAIL}
password = ${MAIL_ADMIN_PASS}
EOF
chmod 600 "${SASPANEL_DIR}/Database/config.ini"
success "Database/config.ini written (chmod 600)."

# Write .env with SECRET_KEY
cat > "${SASPANEL_DIR}/.env" <<EOF
SECRET_KEY=${PANEL_SECRET_KEY}
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=true
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USERNAME=${MAIL_ADMIN_EMAIL}
MAIL_PASSWORD=${MAIL_ADMIN_PASS}
MAIL_USE_TLS=true
EOF
chmod 600 "${SASPANEL_DIR}/.env"
success ".env written with SECRET_KEY (chmod 600)."

# Create logs directory
mkdir -p "${SASPANEL_DIR}/logs"
chown root:root "${SASPANEL_DIR}/logs"
chmod 750 "${SASPANEL_DIR}/logs"

# =============================================================================
# 15. CONFIGURE SYSTEMD SERVICE (Gunicorn, starts on boot)
# =============================================================================
section "Configuring systemd service (Gunicorn)"

cat > /etc/systemd/system/saspanel.service <<EOF
[Unit]
Description=SASPanel — Web Hosting Control Panel
Documentation=https://github.com/mayazhanif/SASPanel
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${SASPANEL_DIR}
EnvironmentFile=${SASPANEL_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn \\
    --workers 4 \\
    --bind 0.0.0.0:5000 \\
    --timeout 120 \\
    --access-logfile ${SASPANEL_DIR}/logs/access.log \\
    --error-logfile ${SASPANEL_DIR}/logs/error.log \\
    app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:${SASPANEL_DIR}/logs/service.log
StandardError=append:${SASPANEL_DIR}/logs/service.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=${SASPANEL_DIR}/logs /home /tmp /var/run /etc/nginx /etc/vsftpd.chroot_list

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable saspanel
systemctl restart saspanel
success "saspanel.service enabled and started (starts on every boot)."

# =============================================================================
# 16. FIREWALL RULES (ufw)
# =============================================================================
section "Configuring firewall (ufw)"

if command -v ufw &>/dev/null; then
    ufw allow 22/tcp    comment 'SSH'
    ufw allow 80/tcp    comment 'HTTP'
    ufw allow 443/tcp   comment 'HTTPS'
    ufw allow 5000/tcp  comment 'SASPanel'
    ufw allow 21/tcp    comment 'FTP'
    ufw allow 25/tcp    comment 'SMTP'
    ufw allow 143/tcp   comment 'IMAP'
    ufw allow 110/tcp   comment 'POP3'
    ufw allow 587/tcp   comment 'SMTPS'
    ufw allow 993/tcp   comment 'IMAPS'
    ufw --force enable
    success "Firewall configured."
else
    warn "ufw not found — configure firewall manually."
fi

# =============================================================================
# 17. FINAL SUMMARY
# =============================================================================
section "Installation Complete!"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║         SASPanel Installation Successful! 🎉          ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Panel URL:${NC}     http://${SERVER_IP}:5000"
echo -e "  ${BOLD}phpMyAdmin:${NC}    http://${SERVER_IP}/phpmyadmin"
echo -e "  ${BOLD}Roundcube:${NC}     http://${SERVER_IP}/roundcube"
echo -e "  ${BOLD}Web FTP:${NC}       http://${SERVER_IP}/webftp"
echo ""
echo -e "${YELLOW}${BOLD}⚠  All credentials saved to: ${CRED_FILE}${NC}"
echo -e "${YELLOW}   Please save them to a password manager, then delete the file:${NC}"
echo -e "${RED}   shred -u ${CRED_FILE}${NC}"
echo ""
echo -e "  ${BOLD}Service status:${NC}  systemctl status saspanel"
echo -e "  ${BOLD}View logs:${NC}       tail -f ${SASPANEL_DIR}/logs/error.log"
echo -e "  ${BOLD}Install log:${NC}     ${LOG_FILE}"
echo ""
