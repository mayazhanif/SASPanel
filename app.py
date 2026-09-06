"""
app.py — SASPanel Flask application entry point (security-hardened)

Security improvements:
  - SECRET_KEY loaded from environment variable (never hardcoded)
  - debug mode controlled by FLASK_DEBUG env var (default: off)
  - Secure session cookie settings (HttpOnly, SameSite, Secure)
  - Flask-WTF CSRF protection enabled globally
  - Flask-Limiter configured (applied per-route in login_routes)
  - Security headers added on every response
  - Mail configured for TLS (port 587)
  - /reboot and /test endpoints removed (see custom_pages.py)
"""

import os
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import configparser

from dotenv import load_dotenv

# Load .env file if present (development convenience)
load_dotenv()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(
    __name__,
    static_url_path='',
    static_folder='apps/static',
    template_folder='apps/templates',
)

# ------------------------------------------------------------------
# Secret key — MUST come from environment; no hardcoded fallback
# ------------------------------------------------------------------
_secret = os.environ.get('SECRET_KEY')
if not _secret:
    raise RuntimeError(
        'SECRET_KEY environment variable is not set. '
        'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
    )
app.secret_key = _secret

# ------------------------------------------------------------------
# Session cookie security
# ------------------------------------------------------------------
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Set to True when serving over HTTPS (recommended for production)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# ------------------------------------------------------------------
# Static file caching — disabled so updates are seen immediately
# ------------------------------------------------------------------
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ------------------------------------------------------------------
# Mail configuration (TLS, port 587)
# ------------------------------------------------------------------
_cfg_dir = os.path.dirname(os.path.abspath(__file__))
_initfile = os.path.join(_cfg_dir, 'Database', 'config.ini')
_config = configparser.RawConfigParser()
_config.read(_initfile)

try:
    _mailDetails = dict(_config.items('mail'))
    app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER',   _mailDetails.get('server', 'localhost'))
    app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', _mailDetails.get('email', ''))
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', _mailDetails.get('password', ''))
    app.config['MAIL_USE_TLS']  = os.environ.get('MAIL_USE_TLS',  'true').lower() == 'true'
    app.config['MAIL_USE_SSL']  = False
except Exception:
    pass  # Mail not configured — will fail gracefully when sending

# ------------------------------------------------------------------
# CSRF protection (Flask-WTF)
# ------------------------------------------------------------------
csrf = CSRFProtect(app)

# ------------------------------------------------------------------
# Rate limiter (Flask-Limiter) — default limit; tighter limits applied per-route
# ------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=['200 per day', '60 per hour'],
    storage_uri='memory://',
)

# ------------------------------------------------------------------
# Blueprint registration
# ------------------------------------------------------------------
from routes.admin_routes import *   # noqa: E402, F401, F403
from routes.login_routes import *   # noqa: E402, F401, F403
from routes.custom_pages import *   # noqa: E402, F401, F403
from routes.user_routes import *    # noqa: E402, F401, F403
from routes.ajax_routes import *    # noqa: E402, F401, F403
from functions import *             # noqa: E402, F401, F403

app.register_blueprint(routes)

# ------------------------------------------------------------------
# Security headers on every response
# ------------------------------------------------------------------
@app.after_request
def add_security_headers(response):
    # Prevent caching of sensitive pages
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma']  = 'no-cache'
    response.headers['Expires'] = '0'
    # Security headers
    response.headers['X-Frame-Options']        = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection']       = '1; mode=block'
    response.headers['Referrer-Policy']        = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']     = 'geolocation=(), microphone=(), camera=()'
    # Content Security Policy — tighten further for your specific JS/CSS sources
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


# ------------------------------------------------------------------
# Context processor — expose host URL to templates
# ------------------------------------------------------------------
@app.context_processor
def server_host():
    # FIX R8-07: use SERVER_NAME from env (trusted config), not request.base_url
    # which is derived from the user-controlled Host: header
    trusted_host = os.environ.get('SERVER_NAME') or request.host
    return dict(mainhost=trusted_host)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', '5000'))
    # For production, use Gunicorn instead:
    #   gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(host='0.0.0.0', port=port, debug=debug_mode)