<div align="center">

<img src="https://img.shields.io/badge/SASPanel-Web%20Hosting%20Control%20Panel-6C63FF?style=for-the-badge&logo=server&logoColor=white"/>

# SASPanel

**A powerful, open-source web hosting control panel built with Python & Flask.**  
Manage domains, databases, FTP accounts, email, SSL certificates and server resources — all from a clean web UI.

[![License](https://img.shields.io/github/license/mayazhanif/SASPanel?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
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
- [Screenshots](#-screenshots)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 👤 **User Management** | Create, update, suspend, and delete hosting users with package limits |
| 📦 **Hosting Packages** | Define resource limits (domains, FTP, mail, databases, storage) |
| 🌐 **Domain Management** | Add domains, auto-configure Nginx vhosts, suspend/unsuspend |
| 🔒 **SSL Certificates** | Let's Encrypt integration — auto-issue and renew |
| 🗄️ **MySQL Databases** | Create/delete databases, change passwords, per-user isolation |
| 📁 **FTP Accounts** | Create FTP users, change passwords, delete accounts |
| 📧 **Email Accounts** | Virtual mail via Postfix + Dovecot, Roundcube webmail |
| ⏰ **Cron Jobs** | Schedule cron jobs per user |
| 📊 **Server Monitoring** | Real-time CPU, RAM, load average, uptime display |
| 🔑 **Admin & User Portals** | Separate dashboards for administrators and end users |
| 🛡️ **Security Hardened** | CSRF protection, rate limiting, bcrypt passwords, security headers |

---

## ⚙️ Requirements

| Component | Version |
|-----------|---------|
| **OS** | Ubuntu 20.04 LTS or 22.04 LTS |
| **Python** | 3.8+ |
| **MySQL** | 8.0+ |
| **Nginx** | 1.18+ |
| **Root Access** | Required for installation |

> ⚠️ **VPS / Dedicated server recommended.** Shared hosting will not work.

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

1. Your panel domain (e.g. `panel.yourdomain.com`) — must already point to the server IP
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

══ Installing Nginx ... MySQL ... PHP ... Postfix ... Dovecot ... ══
...

══ Installation Complete! 🎉 ══

  Panel URL:      http://1.2.3.4:5000
  phpMyAdmin:     http://1.2.3.4/phpmyadmin
  Roundcube:      http://1.2.3.4/roundcube
  Web FTP:        http://1.2.3.4/webftp

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

If you prefer to install step by step:

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
# Set a strong MySQL root password
sudo mysql -u root
```

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR_STRONG_PASSWORD';
CREATE DATABASE saspanel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
FLUSH PRIVILEGES;
EXIT;
```

```bash
# Import the SASPanel schema
mysql -u root -p saspanel < scripts/database.sql
```

### 5. Write the configuration file

```bash
cp scripts/sample.config.ini Database/config.ini
nano Database/config.ini
```

Fill in your real values:

```ini
[config]
host = localhost
user = root
password = YOUR_MYSQL_ROOT_PASSWORD
database = saspanel

[mail]
server = localhost
email = admin@yourdomain.com
password = YOUR_MAIL_PASSWORD
```

```bash
chmod 600 Database/config.ini
```

### 6. Set the `SECRET_KEY` environment variable

```bash
# Generate a strong key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Create the .env file
cat > .env <<EOF
SECRET_KEY=PASTE_GENERATED_KEY_HERE
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=true
EOF

chmod 600 .env
```

### 7. Install and start the systemd service

```bash
# Copy the service file
sudo cp scripts/saspanel.service /etc/systemd/system/saspanel.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable saspanel
sudo systemctl start saspanel
```

### 8. Configure Nginx, Postfix, Dovecot

Refer to the scripts in `scripts/` for configuration templates:

| Script | Purpose |
|--------|---------|
| `scripts/installer.sh` | Nginx + VSFTPD base config |
| `scripts/packages_installer.sh` | Postfix + Dovecot + Roundcube + WebFTP |
| `scripts/mysql_admin.sh` | MySQL root password + schema import |
| `scripts/add_vhost.sh` | Add a new Nginx virtual host |
| `scripts/ssl_certificate_generate.sh` | Issue a Let's Encrypt certificate |
| `scripts/add_cron_job.sh` | Add a user cron job |

---

## ⚙️ Configuration

### Environment Variables (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session signing key — **required, no default** | — |
| `FLASK_ENV` | `production` or `development` | `production` |
| `FLASK_DEBUG` | `0` = off, `1` = on (never enable in production) | `0` |
| `SESSION_COOKIE_SECURE` | `true` = only send cookie over HTTPS | `false` |
| `MAIL_SERVER` | SMTP server hostname | `localhost` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | SMTP login username | — |
| `MAIL_PASSWORD` | SMTP login password | — |
| `MAIL_USE_TLS` | `true` / `false` | `true` |

Copy `.env.example` to get started:

```bash
cp .env.example .env
nano .env
```

### Database Config (`Database/config.ini`)

```ini
[config]
host = localhost
user = root
password = YOUR_STRONG_DB_PASSWORD
database = saspanel

[mail]
server = localhost
email = support@yourdomain.com
password = YOUR_MAIL_PASSWORD
```

> 🔒 **Always** run `chmod 600 Database/config.ini` after editing.

---

## ▶️ Running the Panel

### Via systemd (Production — recommended)

```bash
# Start
sudo systemctl start saspanel

# Stop
sudo systemctl stop saspanel

# Restart
sudo systemctl restart saspanel

# View status
sudo systemctl status saspanel

# View live logs
tail -f /home/SASPanel/logs/error.log
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

> ⚠️ Never use `FLASK_DEBUG=1` in production. It exposes an interactive debugger.

---

## 🛡️ Security

SASPanel has been fully security-hardened. Key protections include:

| Protection | Implementation |
|-----------|---------------|
| **CSRF Protection** | Flask-WTF `CSRFProtect` on all forms |
| **Rate Limiting** | Flask-Limiter — 10 login attempts/minute/IP |
| **Password Hashing** | PBKDF2-SHA256 via Werkzeug (bcrypt-compatible) |
| **Legacy MD5 Migration** | MD5 passwords auto-upgraded to bcrypt on next login |
| **Secret Key** | Loaded from env var only — app refuses to start without it |
| **Security Headers** | `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `X-XSS-Protection`, `Referrer-Policy` |
| **Session Security** | `HttpOnly`, `SameSite=Lax`, optional `Secure` flag |
| **SQL Injection** | All queries use parameterized `%s` placeholders |
| **OS Command Injection** | All shell calls use `subprocess.run(list)` with input validation |
| **Audit Logging** | Security events logged to `logs/audit.log` |
| **Installer Lockout** | `/installer` returns 403 once database is configured |
| **Endpoint Protection** | `/reboot/` requires admin session |
| **Input Validation** | Usernames, domains, DB names validated via strict regex whitelist |

### Reporting a Vulnerability

See [SECURITY.md](SECURITY.md) for our responsible disclosure process.

### Post-Install Hardening Checklist

- [ ] Delete `/root/saspanel_credentials.txt` after saving passwords
- [ ] `chmod 600 Database/config.ini`
- [ ] `chmod 600 .env`
- [ ] Enable HTTPS on port 5000 (place Nginx reverse proxy in front)
- [ ] Set `SESSION_COOKIE_SECURE=true` in `.env` once HTTPS is active
- [ ] Rotate the database password if it was ever committed to git

---

## 📁 Project Structure

```
SASPanel/
├── app.py                    # Flask application factory
├── functions.py              # Core utility functions
├── install.sh                # Automated one-command installer
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
│
├── routes/
│   ├── __init__.py           # Blueprint registration
│   ├── admin_routes.py       # Admin panel routes
│   ├── user_routes.py        # User panel routes
│   ├── login_routes.py       # Authentication routes
│   ├── custom_pages.py       # Misc / installer routes
│   ├── ajax_routes.py        # Server monitoring API
│   └── security.py           # Auth decorators, audit log, sanitizers
│
├── Database/
│   ├── DbConfig.py           # MySQL connection manager
│   ├── config.ini            # DB + mail config (chmod 600, gitignored)
│   └── sample.config.ini     # Template for config.ini
│
├── apps/
│   ├── static/               # CSS, JS, images
│   └── templates/            # Jinja2 HTML templates
│       ├── adminFiles/       # Admin dashboard templates
│       ├── userFiles/        # User dashboard templates
│       ├── authentication/   # Login / reset password
│       ├── installer/        # First-run installer UI
│       └── error_pages/      # 403, 404, 429, 500
│
├── scripts/
│   ├── installer.sh          # Nginx + VSFTPD config
│   ├── packages_installer.sh # Mail stack + Roundcube + WebFTP
│   ├── mysql_admin.sh        # MySQL root setup + schema import
│   ├── add_vhost.sh          # Add Nginx vhost for a domain
│   ├── ssl_certificate_generate.sh  # Issue Let's Encrypt cert
│   ├── add_cron_job.sh       # Add user cron job
│   ├── database.sql          # SASPanel MySQL schema
│   ├── mail.sql              # Virtual mail schema
│   └── saspanel.service      # Systemd service unit
│
└── logs/                     # Runtime logs (gitignored)
    ├── access.log
    ├── error.log
    ├── service.log
    └── audit.log             # Security event audit trail
```

---

## 📸 Screenshots

| Admin Dashboard | User Dashboard |
|----------------|---------------|
| Server monitoring, user list, package management | Domains, databases, FTP, email, cron jobs |

---

## 🔍 Troubleshooting

### Panel won't start — `SECRET_KEY not set`

```bash
# Add SECRET_KEY to your .env file
python3 -c "import secrets; print(secrets.token_hex(32))"
echo "SECRET_KEY=PASTE_RESULT_HERE" >> /home/SASPanel/.env
sudo systemctl restart saspanel
```

### Database connection failed

```bash
# Check MySQL is running
sudo systemctl status mysql

# Verify credentials
mysql -u root -p -e "SHOW DATABASES;"

# Check config.ini
cat /home/SASPanel/Database/config.ini
```

### Panel is running but I get 403 on installer

This means the database is already connected — the installer is intentionally locked. Navigate to `/login` instead.

### Nginx shows 502 Bad Gateway

```bash
# Check if SASPanel is running on port 5000
sudo systemctl status saspanel
curl http://localhost:5000
```

### View logs

```bash
# Application errors
tail -f /home/SASPanel/logs/error.log

# Security events (login attempts, injection attempts, etc.)
tail -f /home/SASPanel/logs/audit.log

# Full install log
cat /var/log/saspanel_install.log
```

### Reset admin password via MySQL

```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YOUR_NEW_PASSWORD'))"

mysql -u root -p saspanel
```
```sql
UPDATE administrator SET Admin_Password = 'PASTE_HASH_HERE' WHERE Admin_Email = 'admin@yourdomain.com';
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **GPL-3.0 License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Made with ❤️ by the SASPanel Team
</div>
