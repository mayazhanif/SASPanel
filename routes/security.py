"""
routes/security.py
------------------
Centralised security utilities for SASPanel.

Provides:
  - @require_admin  — enforces admin session, redirects otherwise
  - @require_user   — enforces user session, redirects otherwise
  - sanitize_shell_arg(value) — strict whitelist for any value passed to shell
  - log_security_event(event, details) — appends to audit.log
"""

import re
import os
import logging
from functools import wraps
from flask import session, redirect, url_for, request

# ---------------------------------------------------------------------------
# Audit logger — writes to logs/audit.log relative to project root
# ---------------------------------------------------------------------------
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(_LOG_DIR, exist_ok=True)

_audit_logger = logging.getLogger('saspanel.audit')
_audit_logger.setLevel(logging.INFO)
if not _audit_logger.handlers:
    _fh = logging.FileHandler(os.path.join(_LOG_DIR, 'audit.log'), encoding='utf-8')
    _fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    _audit_logger.addHandler(_fh)


def log_security_event(event_type: str, details: str = '') -> None:
    """Append a line to the security audit log."""
    ip = request.remote_addr if request else 'unknown'
    user_id = session.get('id', 'anon')
    _audit_logger.info('[%s] ip=%s user_id=%s | %s', event_type, ip, user_id, details)


# ---------------------------------------------------------------------------
# Input sanitizers
# ---------------------------------------------------------------------------

# Strict username whitelist: lowercase letters, digits, underscores, hyphens; max 64 chars
_USERNAME_RE = re.compile(r'^[a-z0-9_-]{1,64}$')

# Domain name whitelist: letters, digits, hyphens, dots; max 253 chars
_DOMAIN_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]{1,251}[a-zA-Z0-9]$')

# Database name whitelist: letters, digits, underscores; max 64 chars
_DBNAME_RE = re.compile(r'^[a-zA-Z0-9_]{1,64}$')

# Email whitelist (basic; also validated by validateEmail in functions.py)
_EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$')

# Cron schedule: a very basic check — 5 space-separated fields
_CRON_RE = re.compile(r'^[\d*/,\-]+ [\d*/,\-]+ [\d*/,\-]+ [\d*/,\-]+ [\d*/,\-]+$')


def sanitize_shell_arg(value: str, kind: str = 'username') -> str:
    """
    Validate *value* against a strict whitelist for the given *kind*.
    Returns the sanitised value on success.
    Raises ValueError if validation fails.

    Supported kinds: 'username', 'domain', 'dbname', 'email', 'cron'
    """
    patterns = {
        'username': _USERNAME_RE,
        'domain': _DOMAIN_RE,
        'dbname': _DBNAME_RE,
        'email': _EMAIL_RE,
        'cron': _CRON_RE,
    }
    pattern = patterns.get(kind)
    if pattern is None:
        raise ValueError(f'Unknown sanitize kind: {kind}')
    if not pattern.match(value):
        log_security_event('INJECTION_ATTEMPT', f'kind={kind} value={value!r}')
        raise ValueError(f'Invalid {kind}: {value!r}')
    return value


# ---------------------------------------------------------------------------
# Auth decorators
# ---------------------------------------------------------------------------

def require_admin(f):
    """Decorator: redirect to login if the current session is not an Admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('loggedin') and session.get('usertype') == 'Admin':
            return f(*args, **kwargs)
        log_security_event('UNAUTH_ADMIN_ACCESS', f'endpoint={request.endpoint}')
        return redirect(url_for('routes.login'))
    return decorated


def require_user(f):
    """Decorator: redirect to login if the current session is not a User."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('loggedin') and session.get('usertype') == 'User':
            return f(*args, **kwargs)
        log_security_event('UNAUTH_USER_ACCESS', f'endpoint={request.endpoint}')
        return redirect(url_for('routes.login'))
    return decorated
