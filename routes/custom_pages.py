"""
routes/custom_pages.py — Miscellaneous page routes (security-hardened)

Changes:
  - /test/ debug endpoint REMOVED
  - /reboot/ endpoint now requires admin authentication
  - Installer locked out once DB is connected (returns 403)
  - Installer form inputs validated before passing to install_packages()
"""

from flask import render_template, redirect, url_for, session, request, abort
from . import routes
from app import app
from Database.DbConfig import mysqlconnection, mysql_connect
from functions import install_packages
from routes.security import require_admin, log_security_event
import subprocess


# ---------------------------------------------------------------------------
# Reboot — admin-only, authenticated
# ---------------------------------------------------------------------------

@routes.route('/reboot/')
@require_admin
def reboot():
    log_security_event('ADMIN_REBOOT', 'Admin triggered service restart')
    subprocess.run(['systemctl', 'restart', 'saspanel'])
    return 'Service restarted.'


# ---------------------------------------------------------------------------
# Installer — available ONLY when DB is not yet configured
# ---------------------------------------------------------------------------

@routes.route('/installer', methods=['POST', 'GET'])
def installer():
    conn = mysql_connect()
    # If DB is already connected, installer is locked — return 403
    if conn is not None:
        abort(403)

    msg = ''
    if request.method == 'POST' \
            and 'DBpass1' in request.form \
            and 'DBpass2' in request.form \
            and 'mailserverpassword' in request.form \
            and 'emailaddress' in request.form \
            and 'domain' in request.form \
            and 'emailpassword' in request.form:

        DBpass1           = request.form['DBpass1']
        DBpass2           = request.form['DBpass2']
        mailserverpassword = request.form['mailserverpassword']
        emailaddress      = request.form['emailaddress']
        emailpassword     = request.form['emailpassword']
        domain            = request.form['domain']

        # Basic length / content validation
        if len(DBpass1) < 12:
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'DB password must be at least 12 characters.'})
        # FIX R23-04: cap max length to prevent DoS via huge password input
        if len(DBpass1) > 128:
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'DB password must be 128 characters or fewer.'})
        if DBpass1 != DBpass2:
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'Password and Confirm Password Mismatch.'})
        # FIX R23-05: validate length of all other password fields before install
        if not (1 <= len(mailserverpassword) <= 128):
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'Mail server password must be 1-128 characters.'})
        if not (1 <= len(emailpassword) <= 128):
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'Email password must be 1-128 characters.'})

        # FIX R12-06: validate full email address properly before passing to install_packages()
        # emailaddress here is the local-part only (before @); domain comes from the domain field
        import re
        _DOMAIN_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]{1,251}[a-zA-Z0-9]$')
        # local-part: start/end with alphanumeric; allow dots, +, -, _ in the middle; max 64 chars
        _LOCALPART_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9.+_-]{0,62}[A-Za-z0-9]$|^[A-Za-z0-9]{1}$')
        if not _DOMAIN_RE.match(domain):
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'Invalid domain name.'})
        if not _LOCALPART_RE.match(emailaddress):
            return render_template('installer/installer.html',
                                   msg={'error': 'danger', 'message': 'Invalid email address prefix. Use only letters, digits, dots, hyphens, and underscores.'})

        full_email = emailaddress + '@' + domain
        install_packages(DBpass1, mailserverpassword, domain, full_email, emailpassword)
        return render_template('installer/installer.html',
                               msg={'error': 'success', 'message': 'Installation Completed. Please Reload.'})

    return render_template('installer/installer.html', msg=msg)


# ---------------------------------------------------------------------------
# Home / root redirect
# ---------------------------------------------------------------------------

@routes.route('/')
def home_route():
    conn = mysql_connect()
    if conn is None:
        return redirect(url_for('routes.installer'))
    if 'loggedin' in session:
        if session.get('usertype') == 'Admin':
            return redirect(url_for('routes.admin_dashboard'))
        elif session.get('usertype') == 'User':
            return redirect(url_for('routes.user_dashboard'))
    return redirect(url_for('routes.login'))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@routes.errorhandler(403)
def forbidden(e):
    return render_template('error_pages/403.html'), 403


@routes.errorhandler(404)
def page_not_found(e):
    return render_template('error_pages/404.html'), 404


@routes.errorhandler(429)
def too_many_requests(e):
    return render_template('error_pages/429.html'), 429


@routes.errorhandler(500)
def internal_error(e):
    return render_template('error_pages/500.html'), 500
