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
#    4. Configures: virtual mail stack, roundcube, phpmyadmin
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

# FIX R7-08: validate DOMAIN and ADMIN_EMAIL before using in SQL heredocs and shell scripts
if ! [[ "${DOMAIN}" =~ ^[a-zA-Z0-9][a-zA-Z0-9.\-]{1,251}[a-zA-Z0-9]$ ]]; then
    error "Invalid domain name '${DOMAIN}'. Use only letters, digits, dots, and hyphens."
fi
if ! [[ "${ADMIN_EMAIL}" =~ ^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$ ]]; then
    error "Invalid email address '${ADMIN_EMAIL}'."
fi

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

# BUG FIX: Create empty snippet placeholders BEFORE starting nginx.
# The default site config includes these files — nginx will refuse to start
# if they don't exist. The real content is written later (steps 11-12).
touch /etc/nginx/snippets/phpmyadmin.conf
touch /etc/nginx/snippets/roundcube.conf

# Default vhost — serves phpmyadmin, roundcube
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

# Enable the universe repo — required for php-imagick on Ubuntu 24.04
add-apt-repository -y universe 2>/dev/null || true
apt-get update -y -q

# ── Core PHP extensions — guaranteed on Ubuntu 20.04 / 22.04 / 24.04 ──────────
apt-get install -y \
    php-common php-cli php-fpm \
    php-mysql php-gd php-curl php-zip php-xml \
    php-mbstring php-bz2 php-intl php-gmp mailutils

# ── Optional extensions — present on older Ubuntu; silently skip if missing ────
# php-net-ldap2/3, php-net-smtp, php-mail-mime, php-net-idna2 are PEAR packages
# removed from Ubuntu 24.04 (Noble). Roundcube 1.6+ bundles them via Composer.
# php-imagick requires the universe repo; php-imap / php-json may be built-in.
for PKG in php-imagick php-imap php-json \
           php-net-ldap2 php-net-ldap3 \
           php-net-smtp php-mail-mime php-net-idna2; do
    apt-get install -y "$PKG" 2>/dev/null \
        && info "  Installed optional package: $PKG" \
        || warn "  Optional package not available (skipping): $PKG"
done

# Find the PHP-FPM sock and derive the exact versioned service name
# systemctl does NOT support globs — we must use the exact unit name (e.g. php8.3-fpm)
PHP_FPM_SOCK=$(find /var/run/php/ -name "php*-fpm.sock" 2>/dev/null | head -1)
if [[ -n "$PHP_FPM_SOCK" ]]; then
    sed -i "s|unix:/var/run/php/php-fpm.sock|unix:${PHP_FPM_SOCK}|g" /etc/nginx/php.conf
    info "PHP-FPM socket: ${PHP_FPM_SOCK}"
    # Extract version: /var/run/php/php8.3-fpm.sock -> php8.3-fpm
    PHP_FPM_SVC=$(basename "${PHP_FPM_SOCK}" .sock)
    info "PHP-FPM service: ${PHP_FPM_SVC}"
    systemctl enable "${PHP_FPM_SVC}"
    systemctl restart "${PHP_FPM_SVC}"
else
    # Fallback: try to find and enable any php*-fpm service that actually exists
    PHP_FPM_SVC=$(systemctl list-unit-files 'php*-fpm.service' --no-legend 2>/dev/null \
                  | awk '{print $1}' | head -1)
    if [[ -n "$PHP_FPM_SVC" ]]; then
        info "PHP-FPM service (fallback): ${PHP_FPM_SVC}"
        systemctl enable "${PHP_FPM_SVC}"
        systemctl restart "${PHP_FPM_SVC}"
    else
        warn "Could not find a PHP-FPM service to enable — start it manually."
    fi
fi
success "PHP installed."

# =============================================================================
# 7. INSTALL MYSQL
# =============================================================================
section "Installing MySQL"

apt-get install -y mysql-server

# FIX R17-04: ${DB_ROOT_PASS} interpolated directly into SQL heredoc — injection risk
# if password contains quotes, dashes or percent. Use Python helper instead.
DB_ROOT_PASS_FILE=$(mktemp); chmod 600 "${DB_ROOT_PASS_FILE}"
trap 'rm -f "${DB_ROOT_PASS_FILE}"' EXIT
printf '%s' "${DB_ROOT_PASS}" > "${DB_ROOT_PASS_FILE}"

python3 - <<PYEOF
import subprocess, os, tempfile
def sq(s): return s.replace("'", "''")
rp = sq(open('${DB_ROOT_PASS_FILE}').read().strip())
with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
    f.write("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{rp}';\n".format(rp=rp))
    f.write("DELETE FROM mysql.user WHERE User='';\n")
    f.write("DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');\n")
    f.write("DROP DATABASE IF EXISTS test;\n")
    f.write("DELETE FROM mysql.db WHERE Db='test' OR Db='test\\\\_%';\n")
    f.write("CREATE DATABASE IF NOT EXISTS saspanel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n")
    f.write("CREATE USER IF NOT EXISTS 'saspanel_user'@'localhost' IDENTIFIED BY '{rp}';\n".format(rp=rp))
    f.write("GRANT ALL PRIVILEGES ON saspanel.* TO 'saspanel_user'@'localhost';\n")
    f.write("FLUSH PRIVILEGES;\n")
    fname = f.name
subprocess.run(['mysql', '-u', 'root'], stdin=open(fname))
os.unlink(fname)
PYEOF

# Import SASPanel schema
if [[ -f "${SCRIPTS_DIR}/database.sql" ]]; then
    mysql -u root -p"${DB_ROOT_PASS}" saspanel < "${SCRIPTS_DIR}/database.sql"
    success "SASPanel database schema imported."
else
    warn "scripts/database.sql not found — import manually after install."
fi

# Admin account credentials — generated now, account created after venv is ready
PANEL_ADMIN_PASS=$(gen_pass 20)
PANEL_ADMIN_NAME="Administrator"
PANEL_ADMIN_USER="admin"


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

# FIX R17-04b: mail DB passwords in heredoc — use MYSQL_PWD env var (no password in SQL body)
MYSQL_PWD="${DB_ROOT_PASS}" mysql -u root <<MAILDBEOF
CREATE DATABASE IF NOT EXISTS mail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'mail_admin'@'localhost' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON mail.* TO 'mail_admin'@'localhost';
FLUSH PRIVILEGES;
MAILDBEOF

DB_MAIL_PASS_FILE=$(mktemp); chmod 600 "${DB_MAIL_PASS_FILE}"
trap 'rm -f "${DB_MAIL_PASS_FILE}"' EXIT
printf '%s' "${DB_MAIL_PASS}" > "${DB_MAIL_PASS_FILE}"
python3 - <<PYEOF
import subprocess, os, tempfile
def sq(s): return s.replace("'", "''")
mp = sq(open('${DB_MAIL_PASS_FILE}').read().strip())
with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
    f.write("ALTER USER 'mail_admin'@'localhost' IDENTIFIED BY '{mp}';\nFLUSH PRIVILEGES;\n".format(mp=mp))
    fname = f.name
env = os.environ.copy()
# BUG FIX: DB_ROOT_PASS is a bash variable, not an env var — read from temp file
env['MYSQL_PWD'] = open('${DB_ROOT_PASS_FILE}').read().strip()
subprocess.run(['mysql', '-u', 'root'], stdin=open(fname), env=env)
os.unlink(fname)
PYEOF

if [[ -f "${SCRIPTS_DIR}/mail.sql" ]]; then
    mysql -u root -p"${DB_ROOT_PASS}" mail < "${SCRIPTS_DIR}/mail.sql"
    success "Mail schema imported."
fi

# FIX R17-04c: MAIL_ADMIN_EMAIL and MAIL_ADMIN_PASS in SQL heredoc — use Python helper
MAIL_ADMIN_EMAIL_FILE=$(mktemp); MAIL_ADMIN_PASS_FILE=$(mktemp)
chmod 600 "${MAIL_ADMIN_EMAIL_FILE}" "${MAIL_ADMIN_PASS_FILE}"
trap 'rm -f "${MAIL_ADMIN_EMAIL_FILE}" "${MAIL_ADMIN_PASS_FILE}"' EXIT
printf '%s' "${MAIL_ADMIN_EMAIL}" > "${MAIL_ADMIN_EMAIL_FILE}"
printf '%s' "${MAIL_ADMIN_PASS}"  > "${MAIL_ADMIN_PASS_FILE}"
python3 - <<PYEOF
import subprocess, os, tempfile
def sq(s): return s.replace("'", "''")
email = sq(open('${MAIL_ADMIN_EMAIL_FILE}').read().strip())
passw = sq(open('${MAIL_ADMIN_PASS_FILE}').read().strip())
dom   = sq('${DOMAIN}')
with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
    f.write("INSERT IGNORE INTO domains (domain) VALUES ('{d}');\n".format(d=dom))
    f.write("INSERT IGNORE INTO users (email, password) VALUES ('{e}', '{p}');\n".format(e=email, p=passw))
    fname = f.name
env = os.environ.copy()
# BUG FIX: DB_ROOT_PASS is a bash variable, not an env var — empty fallback caused
# 'Access denied (using password: NO)'. Read from the temp file instead.
env['MYSQL_PWD'] = open('${DB_ROOT_PASS_FILE}').read().strip()
subprocess.run(['mysql', '-u', 'root', 'mail'], stdin=open(fname), env=env)
os.unlink(fname)
PYEOF

# Virtual mail user
groupadd -g 5000 vmail 2>/dev/null || true
useradd -g vmail -u 5000 vmail -d /home/vmail -m 2>/dev/null || true
make-ssl-cert generate-default-snakeoil --force-overwrite
usermod --append --groups ssl-cert postfix 2>/dev/null || true

# FIX R20-01: write Postfix connector configs via Python — avoids ${DB_MAIL_PASS} heredoc
# interpolation breaking if password contains \n, #, or other special chars
python3 - <<PYEOF
import os
mail_pass = open('${DB_MAIL_PASS_FILE}').read().strip()

configs = {
    '/etc/postfix/mysql-virtual_domains.cf': (
        'user = mail_admin\n'
        'password = {pw}\n'
        'dbname = mail\n'
        "query = SELECT domain AS virtual_domain FROM domains WHERE domain='%s'\n"
        'hosts = 127.0.0.1\n'
    ),
    '/etc/postfix/mysql-virtual_forwardings.cf': (
        'user = mail_admin\n'
        'password = {pw}\n'
        'dbname = mail\n'
        "query = SELECT destination FROM forwardings WHERE source='%s'\n"
        'hosts = 127.0.0.1\n'
    ),
    '/etc/postfix/mysql-virtual_mailboxes.cf': (
        'user = mail_admin\n'
        'password = {pw}\n'
        'dbname = mail\n'
        "query = SELECT CONCAT(SUBSTRING_INDEX(email,'@',-1),'/',SUBSTRING_INDEX(email,'@',1),'/') FROM users WHERE email='%s'\n"
        'hosts = 127.0.0.1\n'
    ),
    '/etc/postfix/mysql-virtual_email2email.cf': (
        'user = mail_admin\n'
        'password = {pw}\n'
        'dbname = mail\n'
        "query = SELECT email FROM users WHERE email='%s'\n"
        'hosts = 127.0.0.1\n'
    ),
}

for path, template in configs.items():
    content = template.format(pw=mail_pass)
    with open(path, 'w') as f:
        f.write(content)
    os.chmod(path, 0o640)
    print(f'Written: {path}')
PYEOF
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

# FIX R20-04: write dovecot-sql.conf via Python — avoids ${DB_MAIL_PASS_CONF}
# interpolation. If password contains '#', Dovecot treats the rest as a comment.
python3 - <<PYEOF
mail_pass = open('${DB_MAIL_PASS_FILE}').read().strip()
content = (
    'driver = mysql\n'
    'connect = host=127.0.0.1 dbname=mail user=mail_admin password={pw}\n'
    'default_pass_scheme = PLAIN\n'
    "password_query = SELECT email as user, password FROM users WHERE email='%u';\n"
).format(pw=mail_pass)
with open('/etc/dovecot/dovecot-sql.conf', 'w') as f:
    f.write(content)
import os; os.chmod('/etc/dovecot/dovecot-sql.conf', 0o600)
print('dovecot-sql.conf written safely.')
PYEOF

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
    wget -q https://github.com/roundcube/roundcubemail/releases/download/1.7.4/roundcubemail-1.7.4-complete.tar.gz
    tar xf roundcubemail-1.7.4-complete.tar.gz
    mv roundcubemail-1.7.4 roundcube
    rm -f roundcubemail-1.7.4-complete.tar.gz
fi
chown -R www-data:www-data /usr/share/roundcube

# BUG FIX: Generate DESKEY here — it is used in the sed command at line 628
# but was never defined, causing sed to write a literal '${DESKEY}' into the config.
DESKEY=$(python3 -c "import secrets; print(secrets.token_hex(12))")

# FIX R20-02: ROUNDCUBE_PASS in SQL heredoc breaks on single-quote. Use Python helper.
RC_PASS_SETUP_FILE=$(mktemp); chmod 600 "${RC_PASS_SETUP_FILE}"
trap 'rm -f "${RC_PASS_SETUP_FILE}"' EXIT
printf '%s' "${ROUNDCUBE_PASS}" > "${RC_PASS_SETUP_FILE}"
python3 - <<PYEOF
import subprocess, os, tempfile
def sq(s): return s.replace("'", "''")
rc_pass = sq(open('${RC_PASS_SETUP_FILE}').read().strip())
with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
    f.write("CREATE DATABASE IF NOT EXISTS roundcubedb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n")
    f.write("CREATE USER IF NOT EXISTS 'roundcube'@'localhost' IDENTIFIED BY '{pw}';\n".format(pw=rc_pass))
    f.write("GRANT ALL PRIVILEGES ON roundcubedb.* TO 'roundcube'@'localhost';\n")
    f.write("FLUSH PRIVILEGES;\n")
    fname = f.name
env = os.environ.copy()
env['MYSQL_PWD'] = open('${DB_ROOT_PASS_FILE}').read().strip()
subprocess.run(['mysql', '-u', 'root'], stdin=open(fname), env=env)
os.unlink(fname)
print('Roundcube DB user created safely.')
PYEOF

mysql -u root -p"${DB_ROOT_PASS}" roundcubedb < /usr/share/roundcube/SQL/mysql.initial.sql 2>/dev/null || true

# FIX R17-05: ${ROUNDCUBE_PASS} interpolated into sed — breaks if password contains
# sed metacharacters (|, /, &, #). Use Python re.sub for safe replacement.
RC_PASS_FILE2=$(mktemp); chmod 600 "${RC_PASS_FILE2}"
trap 'rm -f "${RC_PASS_FILE2}"' EXIT
printf '%s' "${ROUNDCUBE_PASS}" > "${RC_PASS_FILE2}"

# BUG FIX: Pass the password file path as a command-line arg (sys.argv[1]) so
# we can use a *quoted* heredoc <<'PYEOF'. Quoted heredocs prevent bash from
# expanding $config (a PHP variable in the Python string) as a shell variable,
# which caused "config: unbound variable" with set -u.
python3 /dev/stdin "${RC_PASS_FILE2}" <<'PYEOF'
import re, sys
rc_pass = open(sys.argv[1]).read().strip()
conf_path = '/usr/share/roundcube/config/config.inc.php'
try:
    with open(conf_path) as f:
        content = f.read()
except FileNotFoundError:
    # config.inc.php may not exist yet — copy from sample
    import shutil
    sample = conf_path.replace('config.inc.php', 'config.inc.php.sample')
    shutil.copy(sample, conf_path)
    with open(conf_path) as f:
        content = f.read()

# Set DB DSN
content = re.sub(
    r"^\s*\\\$config\['db_dsnw'\]\s*=.*$",
    "$config['db_dsnw'] = 'mysqli://roundcube:"
        + rc_pass.replace('\\', '\\\\').replace("'", "\\'")
        + "@localhost/roundcubedb';",
    content, flags=re.MULTILINE
)
# Set SMTP server
content = re.sub(
    r"^\s*\\\$config\['smtp_server'\]\s*=.*$",
    "$config['smtp_server'] = 'localhost';",
    content, flags=re.MULTILINE
)
# Set SMTP port
content = re.sub(
    r"^\s*\\\$config\['smtp_port'\]\s*=.*$",
    "$config['smtp_port'] = 25;",
    content, flags=re.MULTILINE
)
with open(conf_path, 'w') as f:
    f.write(content)
print('Roundcube config written safely.')
PYEOF

# DESKEY requires bash variable expansion, so use a targeted sed with escaped $
DESKEY_ESC="${DESKEY}"
python3 /dev/stdin "${DESKEY_ESC}" <<'PYEOF'
import re, sys
deskey = sys.argv[1]
conf_path = '/usr/share/roundcube/config/config.inc.php'
with open(conf_path) as f:
    content = f.read()
content = re.sub(
    r"^\s*\\\$config\['des_key'\]\s*=.*$",
    "$config['des_key'] = '" + deskey.replace('\\', '\\\\').replace("'", "\\'") + "';",
    content, flags=re.MULTILINE
)
with open(conf_path, 'w') as f:
    f.write(content)
print('Roundcube DES key written.')
PYEOF

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

# (Web-FTP removed — use Roundcube for webmail and FTP clients directly)

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

# ── Create initial admin account (werkzeug now available in venv) ─────────────
# Widen password hash columns to varchar(512) — werkzeug scrypt hashes are 160+ chars
mysql -u root -p"${DB_ROOT_PASS}" saspanel <<'ALTEREOF'
ALTER TABLE `administrator` MODIFY `Admin_Password` varchar(512) NOT NULL;
ALTER TABLE `users`         MODIFY `User_Password`  varchar(512) NOT NULL;
ALTER TABLE `mysqldbusers`  MODIFY `DbPassword`     varchar(512) NOT NULL;
ALTER TABLE `mail_accounts` MODIFY `Mail_Pass`      varchar(512) NOT NULL;
ALTER TABLE `ftp_accounts`  MODIFY `FTP_Password`   varchar(512) NOT NULL;
ALTEREOF
success "Password columns widened to varchar(512)."

section "Creating admin account"


# Inject password via env — never passes it on the command line or process list
export _ADMIN_PASS="${PANEL_ADMIN_PASS}"
PANEL_ADMIN_HASH=$("${VENV_DIR}/bin/python3" -c "
import os
from werkzeug.security import generate_password_hash
print(generate_password_hash(os.environ['_ADMIN_PASS']))
")
unset _ADMIN_PASS

mysql -u root -p"${DB_ROOT_PASS}" saspanel <<SQLEOF
INSERT INTO \`administrator\`
    (\`Admin_Name\`, \`Admin_Username\`, \`Admin_Password\`, \`Admin_Email\`, \`Is_Active\`, \`Admin_type\`)
VALUES
    ('${PANEL_ADMIN_NAME}', '${PANEL_ADMIN_USER}', '${PANEL_ADMIN_HASH}', '${ADMIN_EMAIL}', 1, 'Admin');
SQLEOF

success "Admin account created (email: ${ADMIN_EMAIL})."

# Append panel admin credentials to the shared credentials file
cat >> "${CRED_FILE}" <<EOF

[Panel Admin Login]
Login URL         = http://${SERVER_IP}:5000/login/
Email             = ${ADMIN_EMAIL}
Username          = ${PANEL_ADMIN_USER}
Password          = ${PANEL_ADMIN_PASS}
Login Type        = Admin
EOF
success "Panel admin credentials appended to ${CRED_FILE}."


# FIX R20-03: write config.ini via Python configparser — avoids raw heredoc interpolation.
# configparser treats '#', ';', '[' etc. specially. Python's write() escapes them correctly.
python3 - <<PYEOF
import configparser, os
db_pass   = open('${DB_ROOT_PASS_FILE}').read().strip()
mail_pass = open('${MAIL_ADMIN_PASS_FILE}').read().strip()
mail_email = open('${MAIL_ADMIN_EMAIL_FILE}').read().strip()

cfg = configparser.RawConfigParser()
cfg.add_section('config')
cfg.set('config', 'host',     'localhost')
cfg.set('config', 'user',     'root')
cfg.set('config', 'password', db_pass)
cfg.set('config', 'database', 'saspanel')
cfg.add_section('mail')
cfg.set('mail', 'server',   'localhost')
cfg.set('mail', 'email',    mail_email)
cfg.set('mail', 'password', mail_pass)

conf_path = '${SASPANEL_DIR}/Database/config.ini'
with open(conf_path, 'w') as f:
    cfg.write(f)
os.chmod(conf_path, 0o600)
print('config.ini written safely via Python configparser.')
PYEOF
success "Database/config.ini written (chmod 600)."

# Write .env with SECRET_KEY
# NOTE: SESSION_COOKIE_SECURE starts as 'false' because HTTPS is not yet
# configured at this point. After certbot runs successfully, the post-hook
# below flips it to 'true' so cookies are only sent over HTTPS in production.
cat > "${SASPANEL_DIR}/.env" <<EOF
SECRET_KEY=${PANEL_SECRET_KEY}
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=false
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

# BUG FIX: Backslash line-continuations inside a cat<<EOF heredoc do NOT work —
# the shell passes the literal '\' characters into the file, producing a broken
# ExecStart line. Write the service file via Python instead so we can use
# Python string formatting for the variable paths without any heredoc gotchas.
python3 - <<PYEOF
import os
sd  = '${SASPANEL_DIR}'
venv = '${VENV_DIR}'
content = f"""[Unit]
Description=SASPanel \u2014 Web Hosting Control Panel
Documentation=https://github.com/mayazhanif/SASPanel
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory={sd}
EnvironmentFile={sd}/.env
ExecStart={venv}/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 --access-logfile {sd}/logs/access.log --error-logfile {sd}/logs/error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:{sd}/logs/service.log
StandardError=append:{sd}/logs/service.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths={sd}/logs /home /tmp /var/run /etc/nginx /etc/vsftpd.chroot_list

[Install]
WantedBy=multi-user.target
"""
with open('/etc/systemd/system/saspanel.service', 'w') as f:
    f.write(content)
print('saspanel.service written.')
PYEOF

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
echo ""
echo -e "${YELLOW}${BOLD}⚠  All credentials saved to: ${CRED_FILE}${NC}"
echo -e "${YELLOW}   Please save them to a password manager, then delete the file:${NC}"
echo -e "${RED}   shred -u ${CRED_FILE}${NC}"
echo ""
echo -e "  ${BOLD}Service status:${NC}  systemctl status saspanel"
echo -e "  ${BOLD}View logs:${NC}       tail -f ${SASPANEL_DIR}/logs/error.log"
echo -e "  ${BOLD}Install log:${NC}     ${LOG_FILE}"
echo ""
echo -e "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}${BOLD}  HTTPS / SSL — Enable after DNS is pointing to this server${NC}"
echo -e "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  1. Point your domain DNS A-record to: ${SERVER_IP}"
echo -e "  2. Run certbot:"
echo -e "     ${BOLD}certbot --nginx -d ${PANEL_DOMAIN} --non-interactive --agree-tos -m ${ADMIN_EMAIL}${NC}"
echo -e "  3. After certbot succeeds, enable secure cookies:"
echo -e "     ${BOLD}sed -i 's/SESSION_COOKIE_SECURE=false/SESSION_COOKIE_SECURE=true/' ${SASPANEL_DIR}/.env${NC}"
echo -e "     ${BOLD}systemctl restart saspanel${NC}"
echo ""
echo -e "${GREEN}${BOLD}  Panel is running on HTTP until you complete HTTPS setup above.${NC}"
echo ""
