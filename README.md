<div align="center">

<img src="https://img.shields.io/badge/SASPanel-Web%20Hosting%20Control%20Panel-6C63FF?style=for-the-badge&logo=server&logoColor=white"/>

# SASPanel

**A powerful, open-source web hosting control panel built with Python & Flask.**
Manage domains, databases, FTP accounts, email, SSL certificates and server resources — all from a clean, modern web UI.

[![License](https://img.shields.io/github/license/mayazhanif/SASPanel?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Security](https://img.shields.io/badge/Security-Hardened-green?style=flat-square&logo=shield)](SECURITY.md)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Quick Install](#-quick-install-recommended)
- [Manual Install](#-manual-install)
- [Configuration](#-configuration)
- [Running the Panel](#-running-the-panel)
- [Security](#-security)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 👤 **User Management** | Create, update, suspend, and delete hosting users with package-based resource limits |
| 📦 **Hosting Packages** | Define per-user limits: domains, FTP accounts, mail accounts, databases, storage |
| 🌐 **Domain Management** | Add domains, auto-configure Nginx vhosts, suspend/unsuspend, optional auto-create FTP & mail |
| 🔒 **SSL Certificates** | Let's Encrypt integration — auto-issue on domain add, bulk renewal |
| 🗄️ **MySQL Databases** | Create/delete databases and users, update passwords, per-user isolation |
| 📁 **FTP Accounts** | Create FTP users via vsFTPd, change passwords, delete accounts |
| 📧 **Email Accounts** | Virtual mailboxes via Postfix + Dovecot, Roundcube webmail link |
| 🌿 **Subdomains** | Create and delete subdomains with automatic Nginx vhost configuration |
| ⏰ **Cron Jobs** | Schedule and manage cron jobs per user |
| 📊 **Server Monitoring** | Real-time CPU, RAM, load average, disk usage, uptime |
| 🔑 **Admin & User Portals** | Fully separate dashboards — admins manage users, users manage their own resources |
| 🛡️ **Security Hardened** | CSRF protection, rate limiting, secure password hashing, Content Security Policy, audit logs |
| 🔄 **AJAX Dynamic UI** | Domain dropdowns filter dynamically by selected user without page reload |

---

## ⚙️ Requirements

| Component | Version |
|-----------|---------|
| **OS** | Ubuntu 22.04 LTS (recommended) or 20.04 LTS |
| **Python** | 3.12+ |
| **MySQL** | 8.0+ |
| **Nginx** | 1.18+ |
| **vsFTPd** | Any recent version |
| **Postfix + Dovecot** | Any recent version |
| **Root Access** | Required for installation |

> ⚠️ **VPS or dedicated server required.** Shared hosting will not work. Minimum 1 GB RAM recommended.

---

## 🚀 Quick Install (Recommended)

The automated installer handles everything — no manual configuration needed.

### Step 1 — Clone the repository

```bash
git clone https://github.com/mayazhanif/SASPanel.git /home/SASPanel
cd /home/SASPanel
```

### Step 2 — Run the installer

```bash
sudo bash install.sh
```

The script will ask you **two questions only**:

1. Your panel domain (e.g. `panel.yourdomain.com`) — must already point to the server IP via DNS
2. Your admin email address (used for Let's Encrypt SSL notifications)

**Everything else is fully automated:**

```
[INFO]  Server public IP: 1.2.3.4
Domain: panel.yourdomain.com
Email:  admin@yourdomain.com

══ Generating secure credentials ══
[OK]    All credentials generated.

══ Saving credentials to /root/saspanel_credentials.txt ══
[OK]    Credentials saved (chmod 600)

══ Installing Nginx ... MySQL ... Postfix ... Dovecot ... vsFTPd ══
...

══ Installation Complete! 🎉 ══

  Panel URL:      http://1.2.3.4:5000
  phpMyAdmin:     http://1.2.3.4/phpmyadmin
  Roundcube:      http://1.2.3.4/roundcube

⚠  All credentials saved to: /root/saspanel_credentials.txt
   shred -u /root/saspanel_credentials.txt
```

### Step 3 — Save your credentials, then delete the file

```bash
# Read and save to your password manager
cat /root/saspanel_credentials.txt

# Securely delete the file
shred -u /root/saspanel_credentials.txt
```

### Step 4 — Open the panel

Navigate to `http://YOUR_SERVER_IP:5000` and log in with your admin credentials.

---

## 🔧 Manual Install

### 1. Install system dependencies

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    mysql-server nginx certbot python3-certbot-nginx \
    php-common php-cli php-fpm php-mysql php-mbstring php-zip php-gd \
    postfix postfix-mysql dovecot-core dovecot-imapd dovecot-pop3d \
    dovecot-lmtpd dovecot-mysql vsftpd acl curl wget git
```

### 2. Clone the repository

```bash
git clone https://github.com/mayazhanif/SASPanel.git /home/SASPanel
cd /home/SASPanel
```

### 3. Create a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. Configure the database

```bash
sudo mysql -u root
```

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR_STRONG_PASSWORD';
CREATE DATABASE saspanel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE mail     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
FLUSH PRIVILEGES;
EXIT;
```

```bash
mysql -u root -p saspanel < scripts/database.sql
mysql -u root -p mail     < scripts/mail.sql
```

### 5. Set environment variables

```bash
cp .env.example .env
nano .env
chmod 600 .env
```

### 6. Configure the database connection

```bash
cp Database/sample.config.ini Database/config.ini
nano Database/config.ini
chmod 600 Database/config.ini
```

### 7. Create the admin account

```bash
source venv/bin/activate
python3 -c "
from werkzeug.security import generate_password_hash
import mysql.connector, configparser
cfg = configparser.ConfigParser()
cfg.read('Database/config.ini')
db = mysql.connector.connect(
    host=cfg['config']['host'], user=cfg['config']['user'],
    password=cfg['config']['password'], database=cfg['config']['database']
)
cur = db.cursor()
cur.execute(
    'INSERT INTO administrator (Admin_Name, Admin_Email, Admin_Password) VALUES (%s,%s,%s)',
    ('Admin', 'admin@yourdomain.com', generate_password_hash('YOUR_ADMIN_PASSWORD'))
)
db.commit()
print('Admin created.')
"
```

### 8. Install and start the systemd service

```bash
sudo cp scripts/saspanel.service /etc/systemd/system/saspanel.service
sudo systemctl daemon-reload
sudo systemctl enable saspanel
sudo systemctl start saspanel
```

### 9. Configure Nginx reverse proxy (optional but recommended)

```nginx
server {
    listen 80;
    server_name panel.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo certbot --nginx -d panel.yourdomain.com
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session signing key — **required, no default** | — |
| `FLASK_ENV` | `production` or `development` | `production` |
| `FLASK_DEBUG` | `0` = off, `1` = on **(never enable in production)** | `0` |
| `SERVER_NAME` | Trusted panel hostname — prevents Host header injection in password reset links | — |
| `MAIL_SERVER` | SMTP server hostname | `localhost` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | SMTP login username | — |
| `MAIL_PASSWORD` | SMTP login password | — |
| `MAIL_USE_TLS` | `true` / `false` | `true` |
| `LOGIN_RATE_LIMIT` | Max login attempts before 429 | `10 per minute` |
| `SESSION_COOKIE_SECURE` | `true` = HTTPS-only cookies | `false` |

```bash
cp .env.example .env
chmod 600 .env
```

### Database Config (`Database/config.ini`)

```ini
[config]
host     = localhost
user     = root
password = YOUR_STRONG_DB_PASSWORD
database = saspanel

[mail]
server   = localhost
email    = support@yourdomain.com
password = YOUR_MAIL_PASSWORD
```

> 🔒 **Always** run `chmod 600 Database/config.ini` after editing.

---

## ▶️ Running the Panel

### Via systemd (Production — recommended)

```bash
sudo systemctl start saspanel
sudo systemctl stop saspanel
sudo systemctl restart saspanel
sudo systemctl status saspanel

# Live logs
tail -f /home/SASPanel/logs/error.log
tail -f /home/SASPanel/logs/audit.log
```

### Via Gunicorn directly

```bash
cd /home/SASPanel
source venv/bin/activate
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 app:app
```

### Via Flask dev server (development only)

```bash
cd /home/SASPanel
source venv/bin/activate
export FLASK_DEBUG=1
python3 app.py
```

> ⚠️ Never use `FLASK_DEBUG=1` in production — it exposes an interactive debugger.

---

## 🛡️ Security

| Protection | Implementation |
|-----------|----------------|
| **CSRF Protection** | Flask-WTF `CSRFProtect` on every POST form and AJAX request |
| **Rate Limiting** | Flask-Limiter — configurable per-IP login throttle (default: 10/min) |
| **Password Hashing** | PBKDF2-SHA256 via Werkzeug; legacy MD5 passwords auto-upgraded on next login |
| **Secret Key Enforcement** | App refuses to start if `SECRET_KEY` is missing or set to a default value |
| **Security Headers** | `X-Frame-Options`, `X-Content-Type-Options`, strict `Content-Security-Policy`, `Referrer-Policy` |
| **CSP Nonces** | Inline scripts require `nonce="{{ csp_nonce }}"` — enforced on every page |
| **Session Security** | `HttpOnly`, `SameSite=Lax`, optional `Secure` flag |
| **SQL Injection** | 100% parameterized queries — no string concatenation |
| **OS Command Injection** | All shell calls use `subprocess.run(list)` with strict regex input validation |
| **IDOR Protection** | Every resource fetch scoped to the logged-in admin/user's own records |
| **Audit Logging** | Security events logged to `logs/audit.log` |
| **Installer Lockout** | `/installer` returns 403 once the database is configured |
| **Input Validation** | Usernames, domains, DB names validated via strict regex whitelist |

### Post-Install Hardening Checklist

- [ ] Delete `/root/saspanel_credentials.txt` after saving passwords
- [ ] `chmod 600 Database/config.ini && chmod 600 .env`
- [ ] Put Nginx in front of port 5000 and issue SSL
- [ ] Set `SESSION_COOKIE_SECURE=true` once HTTPS is active
- [ ] Set `SERVER_NAME` to your panel domain

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## 📁 Project Structure

```
SASPanel/
├── app.py                      # Flask application factory, CSP middleware, blueprint registration
├── functions.py                # Core helpers: FTP, mail, vhost, SSL, DB, password utils
├── install.sh                  # Automated one-command installer
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
│
├── routes/
│   ├── __init__.py             # Flask Blueprint definition
│   ├── admin_routes.py         # All admin panel routes
│   ├── user_routes.py          # All user panel routes
│   ├── login_routes.py         # Authentication (login, logout, password reset)
│   ├── ajax_routes.py          # AJAX endpoints: server stats, domain-by-user lookup
│   ├── custom_pages.py         # Installer, misc pages
│   └── security.py             # Auth helpers, audit log, input sanitizers
│
├── Database/
│   ├── DbConfig.py             # MySQL connection manager (auto-reconnect)
│   ├── config.ini              # DB + mail credentials (chmod 600, gitignored)
│   └── sample.config.ini       # Template for config.ini
│
├── apps/
│   ├── static/
│   │   ├── css/saspanel.css    # Custom sp-* design system (dark theme, CSS variables)
│   │   └── js/                 # csrf-inject.js, panel utilities
│   └── templates/
│       ├── layout/             # adminheader.html, adminfooter.html, footer.html
│       ├── adminFiles/         # Admin templates: Domains, FTP, Mail, Databases, SubDomains, CronJobs
│       ├── userFiles/          # User templates (same sections, user-scoped)
│       ├── authentication/     # Login, password reset
│       ├── installer/          # First-run web installer
│       └── error_pages/        # 403, 404, 429, 500
│
├── scripts/
│   ├── database.sql            # SASPanel MySQL schema
│   ├── mail.sql                # Virtual mail (Postfix/Dovecot) MySQL schema
│   ├── add_vhost.sh            # Add Nginx virtual host for a domain
│   ├── ssl_certificate_generate.sh  # Issue Let's Encrypt certificate
│   ├── add_cron_job.sh         # Add a user cron job
│   └── saspanel.service        # systemd service unit file
│
└── logs/                       # Runtime logs (gitignored)
    ├── error.log
    ├── access.log
    ├── service.log
    └── audit.log               # Security event audit trail
```

---

## 🔍 Troubleshooting

### Panel won't start — `SECRET_KEY not set`

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
echo "SECRET_KEY=PASTE_RESULT_HERE" >> /home/SASPanel/.env
sudo systemctl restart saspanel
```

### Database connection failed

```bash
sudo systemctl status mysql
mysql -u root -p -e "SHOW DATABASES;"
cat /home/SASPanel/Database/config.ini
```

### Panel returns 403 on `/installer`

The installer locks itself once the database is connected. Navigate to `/login` instead.

### Nginx 502 Bad Gateway

```bash
sudo systemctl status saspanel
curl http://localhost:5000
```

### Domain dropdown doesn't populate in Add Email / Add Subdomain forms

Domains load via AJAX from `/ajax/domains_by_user`. Check:

1. The selected user has at least one non-deleted domain
2. Open browser **DevTools → Console** — error messages are now shown inline
3. `tail -f /home/SASPanel/logs/error.log` for server-side errors

### Subdomain shows double domain (e.g. `sub.example.com.example.com`)

Already fixed — pull the latest code and restart.

### FTP or email account creation silently fails

```bash
tail -f /home/SASPanel/logs/error.log
sudo systemctl status vsftpd       # FTP
sudo systemctl status postfix dovecot  # Mail
```

### Reset admin password

```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NEW_PASSWORD'))"
mysql -u root -p saspanel -e "UPDATE administrator SET Admin_Password='HASH' WHERE Admin_Email='admin@yourdomain.com';"
```

### View all logs

```bash
tail -f /home/SASPanel/logs/error.log   # Application errors
tail -f /home/SASPanel/logs/audit.log   # Security events
cat /var/log/saspanel_install.log       # Installer output
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'feat: describe your change'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

**Code style notes:**
- All templates must use the `sp-*` CSS design system (`apps/static/css/saspanel.css`) — no Bootstrap classes
- All `<script>` tags must include `nonce="{{ csp_nonce }}"`
- All DB queries must use parameterized `%s` placeholders
- All shell commands must go through `functions.py` helpers with `_validate()` checks

---

## 📄 License

This project is licensed under the **GPL-3.0 License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Made with ❤️ by the SASPanel Team
</div>
