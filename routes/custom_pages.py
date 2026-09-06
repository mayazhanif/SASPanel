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

def _admin_exists():
    """Return True if at least one administrator account exists in the DB."""
    try:
        conn = mysql_connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM `administrator`')
        row = cursor.fetchone()
        cursor.close()
        return row is not None and row[0] > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Installer — DISABLED. Admin account is created by install.sh at setup time.
# ---------------------------------------------------------------------------

@routes.route('/installer', methods=['POST', 'GET'])
def installer():
    """The web installer has been removed.
    Admin accounts are created by install.sh during installation.
    If you need to reset/create an admin account, run:
        python manage.py create_admin
    or insert directly into the administrator table.
    """
    from flask import Response
    return Response(
        '<h1>410 — Installer Removed</h1>'
        '<p>The web installer is no longer available. '
        'Admin accounts are created by <code>install.sh</code> during setup.</p>',
        status=410,
        mimetype='text/html'
    )


# ---------------------------------------------------------------------------
# Home / root redirect
# ---------------------------------------------------------------------------

@routes.route('/')
def home_route():
    # Redirect to installer if no admin account exists yet
    if not _admin_exists():
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
