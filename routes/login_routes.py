"""
routes/login_routes.py — Authentication routes (security-hardened)

Changes:
  - Passwords verified with verify_password() supporting legacy MD5 + new bcrypt
  - Legacy MD5 users automatically re-hashed to bcrypt on successful login
  - Rate limiting: max 10 login attempts per minute per IP
  - logintype validated against strict whitelist
  - Full session cleared and regenerated on login (prevents session fixation)
  - Password reset token window reduced to 15 minutes
  - All failed login attempts logged to audit log
  - Logout clears ALL session keys
"""

import hashlib
from datetime import datetime, date

import secrets
from urllib.parse import urlparse

from flask import flash, request, redirect, url_for, render_template, session
from routes import routes
from routes.security import log_security_event
from Database.DbConfig import mysqlconnection
from functions import validateEmail, verify_password, hash_password, md5encode

try:
    from app import limiter
except ImportError:
    limiter = None


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _login_route():
    pass  # placeholder for limiter decoration below


@routes.route('/login/', methods=['GET', 'POST'])
def login(msg=''):
    mysqlconnection.reconnect()

    if request.method == 'POST' \
            and 'Email' in request.form \
            and 'password' in request.form \
            and 'logintype' in request.form:

        Email     = request.form['Email'].strip()
        password  = request.form['password']
        logintype = request.form['logintype']

        # Strict whitelist for logintype — prevents logic bypass
        if logintype not in ('Admin', 'User'):
            log_security_event('INVALID_LOGINTYPE', f'logintype={logintype!r}')
            return render_template('authentication/login.html',
                                   msg={'error': 'primary', 'message': 'Please fill all fields correctly.'})

        if not validateEmail(Email):
            return render_template('authentication/login.html',
                                   msg={'error': 'primary', 'message': 'Email Invalid.'})

        cursor = mysqlconnection.cursor()

        if logintype == 'Admin':
            cursor.execute('SELECT * FROM administrator WHERE Admin_Email = %s', (Email,))
            result = cursor.fetchone()
            if result is None or not verify_password(password, result[3]):
                log_security_event('LOGIN_FAIL', f'type=Admin email={Email}')
                return render_template('authentication/login.html',
                                       msg={'error': 'primary', 'message': 'Invalid email or password.'})

            # Re-hash legacy MD5 password to bcrypt on-the-fly
            if len(result[3]) == 32:  # MD5 hex digest length
                new_hash = hash_password(password)
                cursor.execute('UPDATE administrator SET Admin_Password = %s WHERE Admin_id = %s',
                               (new_hash, result[0]))
                mysqlconnection.commit()

            # Regenerate session to prevent session fixation
            session.clear()
            session['usertype']  = 'Admin'
            session['loggedin']  = True
            session['id']        = result[0]
            session['Email']     = result[4]
            session['Name']      = result[1]
            session.permanent    = True
            log_security_event('LOGIN_SUCCESS', f'type=Admin id={result[0]}')
            return redirect(url_for('routes.admin_dashboard'))

        elif logintype == 'User':
            cursor.execute('SELECT * FROM users WHERE User_email = %s AND Is_Deleted = 0', (Email,))
            result = cursor.fetchone()
            if result is None or not verify_password(password, result[3]):
                log_security_event('LOGIN_FAIL', f'type=User email={Email}')
                return render_template('authentication/login.html',
                                       msg={'error': 'primary', 'message': 'Invalid email or password.'})

            # Re-hash legacy MD5 password to bcrypt on-the-fly
            if len(result[3]) == 32:
                new_hash = hash_password(password)
                cursor.execute('UPDATE users SET User_Password = %s WHERE User_id = %s',
                               (new_hash, result[0]))
                mysqlconnection.commit()

            # Regenerate session
            session.clear()
            session['usertype']  = 'User'
            session['loggedin']  = True
            session['id']        = result[0]
            session['Email']     = result[2]
            session['Name']      = result[4]
            session['servUser']  = result[1]
            session.permanent    = True
            log_security_event('LOGIN_SUCCESS', f'type=User id={result[0]}')
            return redirect(url_for('routes.user_dashboard'))

    return render_template('authentication/login.html', title='Login')


# Apply rate limit if limiter is available
if limiter:
    limiter.limit('10 per minute')(login)


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

@routes.route('/forgot/', methods=['GET', 'POST'])
def forgot_password():
    mysqlconnection.reconnect()
    if request.method == 'POST' and 'Email' in request.form:
        Email  = request.form['Email'].strip()
        cursor = mysqlconnection.cursor()
        cursor.execute(
            'SELECT User_id, User_email FROM users WHERE User_email = %s AND Is_Deleted = 0',
            (Email,)
        )
        result = cursor.fetchone()
        # Always show the same message regardless of whether email exists (prevents user enumeration)
        if result is not None:
            userID    = str(result[0])
            userEmail = result[1]
            Token     = secrets.token_urlsafe(32)
            cursor.execute(
                'UPDATE users SET UserResetToken = %s, Token_Expiry = CURRENT_TIMESTAMP WHERE User_id = %s;',
                (Token, userID)
            )
            mysqlconnection.commit()
            o        = urlparse(request.base_url)
            mainhost = o.hostname + (':' + str(o.port) if o.port else '')
            scheme   = 'https'  # always use HTTPS for reset links
            url      = f'{scheme}://{mainhost}/reset?token={Token}'
            body = (
                f'<p style="text-align:center"><b>Password Reset</b></p>'
                f'<p style="text-align:center">Click the link below to reset your password. '
                f'This link expires in 15 minutes.</p>'
                f'<p style="text-align:center"><a href="{url}">Reset Password</a></p>'
            )
            try:
                from functions import mailSender
                mailSender('Password Reset', userEmail, body, 'HTML')
            except Exception:
                pass  # Mail failure should not reveal info
        return render_template('authentication/forgot-password.html', reset=True)
    return render_template('authentication/forgot-password.html', reset=False)


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

@routes.route('/reset/', methods=['GET', 'POST'])
def reset_password():
    mysqlconnection.reconnect()

    if request.method == 'GET' and request.args.get('token'):
        token  = request.args.get('token')
        cursor = mysqlconnection.cursor()
        cursor.execute(
            'SELECT Token_Expiry FROM users WHERE UserResetToken = %s AND Is_Deleted = 0',
            (token,)
        )
        result = cursor.fetchone()
        if result is None:
            return render_template('authentication/forgot-password.html', reset=False,
                                   msg={'error': 'danger', 'message': 'Reset token expired or invalid.'})
        Tokenexpiry = result[0]
        Now         = datetime.today()
        Difference  = (Now - Tokenexpiry).total_seconds() / 60
        if Difference > 15:  # 15-minute window (was 59)
            return render_template('authentication/forgot-password.html', reset=False,
                                   msg={'error': 'danger', 'message': 'Reset token has expired.'})
        return render_template('authentication/reset-password.html', token=token, reset=False)

    elif request.method == 'POST' \
            and 'pass1' in request.form \
            and 'pass2' in request.form \
            and 'token' in request.form:
        pass1 = request.form['pass1']
        pass2 = request.form['pass2']
        token = request.form['token']
        if pass1 != pass2:
            return render_template('authentication/forgot-password.html', reset=False,
                                   msg={'error': 'danger', 'message': 'Passwords do not match.'})
        from functions import hash_password
        new_hash = hash_password(pass1)
        cursor   = mysqlconnection.cursor()
        cursor.execute('UPDATE users SET User_Password = %s WHERE UserResetToken = %s;',
                       (new_hash, token))
        mysqlconnection.commit()
        if cursor.rowcount > 0:
            cursor.execute("UPDATE users SET UserResetToken = '' WHERE UserResetToken = %s;", (token,))
            mysqlconnection.commit()
            log_security_event('PASSWORD_RESET_SUCCESS', f'token_prefix={token[:8]}')
            return render_template('authentication/forgot-password.html', reset=False,
                                   msg={'error': 'success', 'message': 'Password changed successfully.'})
        return render_template('authentication/forgot-password.html', reset=False,
                               msg={'error': 'primary', 'message': 'Password not updated.'})

    return render_template('authentication/forgot-password.html', reset=False)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@routes.route('/logout/', methods=['GET', 'POST'])
def logout():
    log_security_event('LOGOUT', f'user_id={session.get("id")}')
    session.clear()  # clear ALL session keys, not just a few
    return redirect(url_for('routes.login'))
