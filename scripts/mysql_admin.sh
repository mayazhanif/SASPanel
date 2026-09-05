#!/bin/bash
# mysql_admin.sh — Bootstrap MySQL root + saspanel database
# SH-07 FIX:
#   - Password read from MYSQL_NEW_ROOT_PASS env var (set by functions.py)
#   - Never passed as $1 CLI arg (would appear in `ps aux`)
#   - mysql commands use MYSQL_PWD env var to avoid -p on command line

set -euo pipefail
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

# SH-07 FIX: read password from environment variable set by Python's set_mysql_root()
: "${MYSQL_NEW_ROOT_PASS:?MYSQL_NEW_ROOT_PASS env var is required}"

echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
echo "postfix postfix/mailname string mail.saspanel.org"       | debconf-set-selections
echo "dovecot-core dovecot-core/create-ssl-cert boolean true"  | debconf-set-selections

# SH-07 FIX: Use MYSQL_PWD env var — password never visible in process list
MYSQL_PWD="" mysql -u root <<SQL
CREATE USER IF NOT EXISTS 'root'@'localhost' IDENTIFIED BY '${MYSQL_NEW_ROOT_PASS}';
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY '${MYSQL_NEW_ROOT_PASS}';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';
CREATE DATABASE IF NOT EXISTS saspanel;
FLUSH PRIVILEGES;
SQL

# Restore saspanel schema
MYSQL_PWD="${MYSQL_NEW_ROOT_PASS}" mysql -u root saspanel < /home/SASPanel/scripts/database.sql

# Set root password via ALTER USER (most compatible with MySQL 8+)
MYSQL_PWD="" mysql -u root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_NEW_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL

echo "Restarting MySQL..."
service mysql restart
echo "MySQL root password set successfully."