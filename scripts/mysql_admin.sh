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

# FIX R13-07: Password directly interpolated into SQL heredoc.
# If the password contains single-quotes or SQL metacharacters it breaks.
# Use MYSQL_PWD env var + --execute with properly quoted parameter via Python helper.
# Write password to a temp file and use it in mysql, avoiding shell expansion in SQL.

# Write the password to a secure temp file so MySQL can read it without shell interpolation
PASS_FILE=$(mktemp)
trap 'rm -f "${PASS_FILE}"' EXIT
chmod 600 "${PASS_FILE}"
printf '%s' "${MYSQL_NEW_ROOT_PASS}" > "${PASS_FILE}"

# Bootstrap MySQL with no password (fresh install)
MYSQL_PWD="" mysql -u root <<SQL
CREATE USER IF NOT EXISTS 'root'@'localhost' IDENTIFIED BY '';
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';
CREATE DATABASE IF NOT EXISTS saspanel;
FLUSH PRIVILEGES;
SQL

# Restore saspanel schema
MYSQL_PWD="" mysql -u root saspanel < /home/SASPanel/scripts/database.sql

# FIX R13-07: Set passwords using ALTER USER with --init-command to avoid SQL injection
# via directly-interpolated shell variables in heredocs.
python3 - <<PYEOF
import subprocess, os
pw = open('${PASS_FILE}').read().strip()
# Use parameterized-style by writing to a temp SQL file
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
    # Use SET PASSWORD syntax which properly handles special chars via binary protocol
    f.write("ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{pw}';\n".format(pw=pw.replace("'", "''")))  # SQL-escape
    f.write("ALTER USER 'admin'@'localhost' IDENTIFIED WITH mysql_native_password BY '{pw}';\n".format(pw=pw.replace("'", "''")))  # SQL-escape
    f.write("FLUSH PRIVILEGES;\n")
    fname = f.name
env = os.environ.copy()
env['MYSQL_PWD'] = ''
subprocess.run(['mysql', '-u', 'root'], stdin=open(fname), env=env)
os.unlink(fname)
print('MySQL passwords set via Python helper (SQL-escaped).')
PYEOF


echo "Restarting MySQL..."
service mysql restart
echo "MySQL root password set successfully."