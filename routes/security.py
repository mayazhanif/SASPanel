"""
routes/security.py
------------------
Centralised security utilities for SASPanel.

Provides:
  - @require_admin  — enforces admin session, redirects otherwise
  - @require_user   — enforces user session, redirects otherwise
  - sanitize_shell_arg(value, kind) — strict whitelist for any value passed to shell
  - validate_log_filename(domain_name, user_id, cursor) — safe log path resolution
  - sanitize_cron_command(cmd) — block shell metacharacters in cron commands
  - sanitize_log_filename(name) — strip path traversal from log filenames
  - safe_log_path(base_dir, filename) — resolve + jail path to base_dir
  - log_security_event(event, details) — appends to audit.log
"""

import re
import os
import html
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

# Domain / subdomain name whitelist: letters, digits, hyphens, dots; max 253 chars
_DOMAIN_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]{1,251}[a-zA-Z0-9]$')

# Subdomain suffix (label only, no dots): letters, digits, hyphens; 1–63 chars
_SUFFIX_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$')

# Database name whitelist: letters, digits, underscores; max 64 chars
_DBNAME_RE = re.compile(r'^[a-zA-Z0-9_]{1,64}$')

# Email whitelist (basic; also validated by validateEmail in functions.py)
_EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$')

# Cron schedule: a very basic check — 5 space-separated fields
_CRON_RE = re.compile(r'^[\d*/,\-]+ [\d*/,\-]+ [\d*/,\-]+ [\d*/,\-]+ [\d*/,\-]+$')

# Log filename: only safe chars, no path separators, no null bytes; max 128 chars
_LOGFILE_RE = re.compile(r'^[a-zA-Z0-9._-]{1,128}$')

# Shell metacharacters that must never appear in a cron command
_SHELL_METACHAR_RE = re.compile(r'[;&|`$(){}<>\n\r\x00]')


def sanitize_shell_arg(value: str, kind: str = 'username') -> str:
    """
    Validate *value* against a strict whitelist for the given *kind*.
    Returns the sanitised value on success.
    Raises ValueError if validation fails.

    Supported kinds: 'username', 'domain', 'suffix', 'dbname', 'email', 'cron', 'logfile'
    """
    patterns = {
        'username': _USERNAME_RE,
        'domain':   _DOMAIN_RE,
        'suffix':   _SUFFIX_RE,
        'dbname':   _DBNAME_RE,
        'email':    _EMAIL_RE,
        'cron':     _CRON_RE,
        'logfile':  _LOGFILE_RE,
    }
    pattern = patterns.get(kind)
    if pattern is None:
        raise ValueError(f'Unknown sanitize kind: {kind}')
    if not pattern.match(value):
        log_security_event('INJECTION_ATTEMPT', f'kind={kind} value={value!r}')
        raise ValueError(f'Invalid {kind}: {value!r}')
    return value


def sanitize_cron_command(cmd: str) -> str:
    """
    Block shell metacharacters in a cron command.
    Raises ValueError if the command contains dangerous characters.
    Only allow: printable ASCII except ; & | ` $ ( ) { } < > newline null
    """
    if _SHELL_METACHAR_RE.search(cmd):
        log_security_event('CRON_INJECTION_ATTEMPT', f'cmd={cmd!r}')
        raise ValueError('Cron command contains forbidden shell metacharacters.')
    if len(cmd) > 512:
        raise ValueError('Cron command is too long (max 512 chars).')
    return cmd


def sanitize_log_filename(name: str) -> str:
    """
    Strip path traversal and validate a log filename / domain name used in file paths.
    Allows: letters, digits, dots, hyphens, underscores. Max 253 chars.
    Raises ValueError on anything suspicious.
    """
    if not name:
        raise ValueError('Log filename cannot be empty.')
    # Strip any leading slashes or path components
    name = os.path.basename(name)
    if not _DOMAIN_RE.match(name):
        log_security_event('PATH_TRAVERSAL_ATTEMPT', f'log_filename={name!r}')
        raise ValueError(f'Invalid log filename: {name!r}')
    return name


def safe_log_path(base_dir: str, filename: str, suffix: str = '') -> str:
    """
    Safely construct a file path inside *base_dir*, preventing directory traversal.
    Resolves the real path and asserts it starts with base_dir.
    Raises ValueError if the resolved path escapes the jail.
    """
    joined = os.path.realpath(os.path.join(base_dir, filename + suffix))
    real_base = os.path.realpath(base_dir)
    if not joined.startswith(real_base + os.sep) and joined != real_base:
        log_security_event('PATH_TRAVERSAL_ATTEMPT', f'base={base_dir!r} file={filename!r}')
        raise ValueError(f'Path traversal detected: {filename!r}')
    return joined


def sanitize_log_content(text: str) -> str:
    """
    HTML-escape log content before returning in JSON/HTML responses.
    Prevents second-order XSS via injected log lines.
    """
    return html.escape(str(text))


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
