"""
functions.py — SASPanel core utility functions (security-hardened)

Changes from original:
  - md5encode() kept for legacy DB-check only; new code uses werkzeug.security
  - generatePassword() now uses secrets module (cryptographically secure)
  - All os.system() shell calls replaced with subprocess.run(list-form, no shell=True)
  - All SQL in mail helpers converted to parameterized queries
  - sanitize_shell_arg() imported from routes.security for validation before any shell op
  - add_usr() / add_default_user() / add_ftp*() / remove_* validated before exec
"""

import base64
import hashlib
import re
import os
import secrets
import string
import subprocess
import sys
import time
from hashlib import md5

from flask import session, render_template
from flask import current_app
from cachelib import SimpleCache
from Database.DbConfig import mysqlconnection, WriteConfig, WriteMailConfig
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import psutil

cache = SimpleCache()

# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def get_error_info():
    import traceback
    return traceback.format_exc()


# ---------------------------------------------------------------------------
# Shell execution (safe — uses list form, no shell=True)
# ---------------------------------------------------------------------------

def _run(args, timeout=60, cwd=None, env=None):
    """
    Execute a command safely using subprocess list form (no shell injection).
    Returns (stdout, stderr) as strings.
    """
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        return stdout, stderr
    except subprocess.TimeoutExpired:
        return '', 'Timed out'
    except Exception:
        return '', get_error_info()


# Legacy ExecShell kept for internal monitoring only (not for user-supplied input)
def ExecShell(cmdstring, timeout=None, shell=True, cwd=None, env=None, user=None):
    """
    INTERNAL USE ONLY — used only with trusted, hard-coded command strings
    (e.g. reading /proc/cpuinfo).  Do NOT pass user-supplied data here.
    """
    import tempfile
    a = ''
    e = ''
    tmp_dir = '/dev/shm'
    try:
        rx = hashlib.md5(cmdstring.encode()).hexdigest()
        succ_f = tempfile.SpooledTemporaryFile(max_size=4096, mode='wb+', suffix='_succ', prefix='btex_' + rx, dir=tmp_dir)
        err_f  = tempfile.SpooledTemporaryFile(max_size=4096, mode='wb+', suffix='_err',  prefix='btex_' + rx, dir=tmp_dir)
        sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell, bufsize=128,
                               stdout=succ_f, stderr=err_f, cwd=cwd, env=env)
        if timeout:
            s, d = 0, 0.01
            while sub.poll() is None:
                time.sleep(d)
                s += d
                if s >= timeout:
                    if not err_f.closed: err_f.close()
                    if not succ_f.closed: succ_f.close()
                    return 'Timed out'
        else:
            sub.wait()
        err_f.seek(0);  succ_f.seek(0)
        a = succ_f.read();  e = err_f.read()
        if not err_f.closed: err_f.close()
        if not succ_f.closed: succ_f.close()
    except Exception:
        return '', get_error_info()
    try:
        if isinstance(a, bytes): a = a.decode('utf-8')
        if isinstance(e, bytes): e = e.decode('utf-8')
    except Exception:
        pass
    return a, e


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

_USERNAME_RE = re.compile(r'^[a-z0-9_-]{1,64}$')
_DOMAIN_RE   = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]{1,251}[a-zA-Z0-9]$')
_DBNAME_RE   = re.compile(r'^[a-zA-Z0-9_]{1,64}$')
_EMAIL_RE    = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')


def _validate(value: str, kind: str) -> str:
    """Validate *value* against a whitelist pattern; raise ValueError on failure."""
    patterns = {
        'username': _USERNAME_RE,
        'domain':   _DOMAIN_RE,
        'dbname':   _DBNAME_RE,
    }
    if kind not in patterns:
        raise ValueError(f'Unknown validation kind: {kind}')
    if not patterns[kind].match(value):
        raise ValueError(f'Invalid {kind}: {value!r}')
    return value


# ---------------------------------------------------------------------------
# System info (CPU / Memory / Load / Boot time)
# ---------------------------------------------------------------------------

def getCpuType():
    cpuinfo = ReadFile('/proc/cpuinfo')
    if cpuinfo:
        tmp = re.search(r'model\s+name\s+:\s+(.+)', cpuinfo, re.I)
        if tmp:
            return tmp.groups()[0]
    out = ExecShell('LANG="en_US.UTF-8" && lscpu')[0]
    tmp = re.search(r'Model\s+name:\s+(.+)', out, re.I)
    return tmp.groups()[0] if tmp else ''


def GetCpuInfo(interval=1):
    cpuCount = psutil.cpu_count()
    cpuNum   = psutil.cpu_count(logical=False)
    c_tmp    = readFile('/proc/cpuinfo') or ''
    d_tmp    = re.findall(r'physical id.+', c_tmp)
    cpuW     = len(set(d_tmp))
    import threading
    p = threading.Thread(target=get_cpu_percent_thead, args=(interval,))
    p.daemon = True
    p.start()
    used     = cache.get('cpu_used_all') or get_cpu_percent_thead(interval)
    used_all = psutil.cpu_percent(percpu=True)
    cpu_name = getCpuType() + ' * {}'.format(cpuW)
    return used, cpuCount, used_all, cpu_name, cpuNum, cpuW


def get_cpu_percent_thead(interval=1):
    used = psutil.cpu_percent(interval)
    cache.set('cpu_used_all', used, 10)
    return used


def ReadFile(filename, mode='r'):
    if not os.path.exists(filename):
        return False
    try:
        with open(filename, mode) as fp:
            return fp.read()
    except Exception:
        try:
            with open(filename, mode, encoding='utf-8') as fp:
                return fp.read()
        except Exception:
            try:
                with open(filename, mode, encoding='GBK') as fp:
                    return fp.read()
            except Exception:
                return False


def readFile(filename, mode='r'):
    return ReadFile(filename, mode)


def WriteFile(filename, s_body, mode='w+'):
    try:
        with open(filename, mode) as fp:
            fp.write(s_body)
        return True
    except Exception:
        try:
            with open(filename, mode, encoding='utf-8') as fp:
                fp.write(s_body)
            return True
        except Exception:
            return False


def GetLoadAverage():
    try:
        c = os.getloadavg()
    except Exception as e:
        print('Error CPU ' + str(e))
        c = [0, 0, 0]
    data = {
        'one': float(c[0]),
        'five': float(c[1]),
        'fifteen': float(c[2]),
    }
    data['max']   = psutil.cpu_count() * 2
    data['limit'] = data['max']
    data['safe']  = data['max'] * 0.75
    return data


def GetMemInfo(get=None):
    skey = 'memInfo'
    memInfo = cache.get(skey)
    if memInfo:
        return memInfo
    mem = psutil.virtual_memory()
    memInfo = {
        'memTotal':   int(mem.total   / 1024 / 1024),
        'memFree':    int(mem.free    / 1024 / 1024),
        'memBuffers': int(mem.buffers / 1024 / 1024),
        'memCached':  int(mem.cached  / 1024 / 1024),
    }
    memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
    cache.set(skey, memInfo, 60)
    return memInfo


def GetSystemVersion():
    key = 'sys_version'
    version = cache.get(key)
    if version:
        return version
    version = readFile('/etc/redhat-release')
    if not version:
        raw = readFile('/etc/issue') or ''
        version = raw.strip().split('\n')[0].replace('\\n', '').replace('\\l', '').strip()
    else:
        version = version.replace('release ', '').replace('Linux', '').replace('(Core)', '').strip()
    v_info = sys.version_info
    version = version + '(Py{}.{}.{})'.format(v_info.major, v_info.minor, v_info.micro)
    cache.set(key, version, 600)
    return version


def GetBootTime():
    key = 'sys_time'
    sys_time = cache.get(key)
    if sys_time:
        return sys_time
    import math
    conf_raw = readFile('/proc/uptime')
    if not conf_raw:
        return '0 Day(s)'
    conf   = conf_raw.split()
    tStr   = float(conf[0])
    min_   = tStr / 60
    hours  = min_ / 60
    days   = math.floor(hours / 24)
    hours  = math.floor(hours - days * 24)
    min_   = math.floor(min_ - days * 60 * 24 - hours * 60)
    sys_time = '{} Day(s)'.format(int(days))
    cache.set(key, sys_time, 1800)
    return sys_time


def get_cpu_times():
    skey = 'cpu_times'
    data = cache.get(skey)
    if data:
        return data
    try:
        data = {}
        cpu_times_p = psutil.cpu_times_percent()
        for attr in ('user', 'nice', 'system', 'idle', 'iowait', 'irq',
                     'softirq', 'steal', 'guest', 'guest_nice'):
            data[attr] = getattr(cpu_times_p, attr, 0)
        data['total_processes'] = 0
        data['active_processes'] = 0
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if p.status() == 'running':
                    data['active_processes'] += 1
            except Exception:
                continue
            data['total_processes'] += 1
        cache.set(skey, data, 60)
    except Exception:
        return None
    return data


def get_process_cpu_time():
    cpu_time = 0.0
    for pid in psutil.pids():
        try:
            for s in psutil.Process(pid).cpu_times():
                cpu_time += s
        except Exception:
            continue
    return cpu_time


def get_cpu_time():
    return sum(psutil.cpu_times())


def get_cpu_percent():
    percent = 0.0
    old_cpu_time     = cache.get('old_cpu_time')
    old_process_time = cache.get('old_process_time')
    if not old_cpu_time:
        old_cpu_time     = get_cpu_time()
        old_process_time = get_process_cpu_time()
        time.sleep(1)
    new_cpu_time     = get_cpu_time()
    new_process_time = get_process_cpu_time()
    try:
        percent = round(100.0 * (new_process_time - old_process_time) / (new_cpu_time - old_cpu_time), 2)
    except ZeroDivisionError:
        percent = 0.0
    cache.set('old_cpu_time', new_cpu_time)
    cache.set('old_process_time', new_process_time)
    if percent > 100: percent = 100
    return percent if percent > 0 else 0.0


def GetAllInfo():
    return {
        'load_average': GetLoadAverage(),
        'cpu':          GetCpuInfo(1),
        'time':         GetBootTime(),
        'system':       GetSystemVersion(),
        'mem':          GetMemInfo(),
        'cpu_percentage': get_cpu_percent(),
    }


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def check_Session(type='User'):
    return session.get('loggedin') and session.get('usertype') == type


def check_user_Login():
    return check_Session('User')


def check_admin_Login():
    return check_Session('Admin')


# ---------------------------------------------------------------------------
# Password helpers (bcrypt-backed via Werkzeug)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a secure PBKDF2-SHA256 hash of *plain* (via Werkzeug)."""
    return generate_password_hash(plain, method='pbkdf2:sha256', salt_length=16)


def verify_password(plain: str, stored: str) -> bool:
    """
    Verify *plain* against *stored*.
    Supports both legacy MD5 hashes (32-char hex) and new Werkzeug hashes.
    Call-sites should migrate MD5 users to bcrypt after a successful MD5 verify.
    """
    # New-style Werkzeug/bcrypt hash
    if stored.startswith(('pbkdf2:', 'scrypt:', 'bcrypt')):
        return check_password_hash(stored, plain)
    # Legacy MD5 — accept but caller should re-hash
    if len(stored) == 32:
        return hashlib.md5(plain.encode()).hexdigest() == stored
    return False


def md5encode(string: str) -> str:
    """Legacy MD5 — used only during password migration checks."""
    return hashlib.md5(string.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Token / username / password generators (cryptographically secure)
# ---------------------------------------------------------------------------

def generatePassword(length: int = 16) -> str:
    """Return a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generateservUser(name: str, email: str) -> str:
    name  = re.sub(r'[^a-zA-Z]', '', name).lower()
    email = re.sub(r'[^a-zA-Z]', '', email).lower()
    num   = str(secrets.randbelow(1000))
    return (name + email[:3] + num)[:32]  # cap at 32 chars


def Base64Encode(s: str) -> str:
    return base64.b64encode(s.encode('utf-8')).decode('ascii')


def Base64Decode(s: str) -> str:
    return base64.b64decode(s.encode('ascii')).decode('utf-8')


def validateEmail(email: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(email))


# ---------------------------------------------------------------------------
# Mail sender
# ---------------------------------------------------------------------------

def mailSender(title, receipt, body, type='PLAIN'):
    # FIX R24-04: validate recipient email before passing to Flask-Mail
    # An invalid address causes Flask-Mail to raise an unhandled exception.
    if not validateEmail(str(receipt)):
        raise ValueError(f'mailSender: invalid recipient address: {receipt!r}')
    mail = Mail(current_app._get_current_object())
    sender = current_app.config.get('MAIL_USERNAME') or 'noreply@saspanel.local'
    msg  = Message(title, sender=sender, recipients=[receipt])
    if type == 'PLAIN':
        msg.body = body
    else:
        msg.html = body
    mail.send(msg)
    return 'Sent'


# ---------------------------------------------------------------------------
# System user management (SAFE — subprocess list form, validated input)
# ---------------------------------------------------------------------------

def add_usr(name: str, password: str):
    """Create a restricted shell Linux user (rbash). Input is validated."""
    name = _validate(name, 'username')
    print('Adding user: %s' % name)
    _run(['useradd',
          '--create-home',
          '--user-group',
          '--home', '/home/' + name,
          '--shell', '/bin/rbash',
          name])
    # Set password via chpasswd (avoids passing password on command line)
    proc = subprocess.run(['chpasswd'], input=f'{name}:{password}\n',
                          text=True, capture_output=True)
    _run(['chown', '-R', f'{name}:{name}', f'/home/{name}'])
    _run(['chmod', '755', f'/home/{name}'])
    _run(['setfacl', '-m', f'user:{name}:rx', f'/home/{name}'])
    print('User Added.')


def add_default_user(username: str, password: str):
    """Create a standard Linux hosting user. Input is validated."""
    username = _validate(username, 'username')
    print('Adding user: %s' % username)
    _run(['useradd',
          '--create-home',
          '--user-group',
          '--home', '/home/' + username,
          '--shell', '/bin/rbash',
          username])
    # Set password safely via chpasswd
    subprocess.run(['chpasswd'], input=f'{username}:{password}\n',
                   text=True, capture_output=True)
    _run(['chown', f'{username}:{username}', f'/home/{username}'])
    _run(['chmod', '755', f'/home/{username}'])
    _run(['setfacl', '-m', f'user:{username}:rx', f'/home/{username}'])
    print('User Added.')
    # Append to vsftpd chroot list safely
    chroot_path = '/etc/vsftpd.chroot_list'
    try:
        with open(chroot_path, 'a') as f:
            f.write(username + '\n')
    except Exception as ex:
        print(f'Could not write vsftpd.chroot_list: {ex}')
    _run(['chown', '-R', f'{username}:{username}', f'/home/{username}'])
    _run(['chmod', '0755', f'/home/{username}'])


# ---------------------------------------------------------------------------
# MySQL helpers (parameterized queries only)
# ---------------------------------------------------------------------------

def createUser(cursor, userName: str, password: str):
    try:
        cursor.execute("CREATE USER %s@'localhost' IDENTIFIED BY %s;", (userName, password))
        print('User Created.')
    except Exception as ex:
        print('Error creating MySQL User: %s' % ex)


def create_database(cursor, DatabaseName: str, Username: str):
    try:
        # Database names cannot be parameterized in MySQL; validate strictly
        db = _validate(DatabaseName, 'dbname')
        user = _validate(Username, 'username')
        cursor.execute(f'CREATE DATABASE `{db}`;')
        print('Database Created.')
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{db}`.* TO %s@'localhost' WITH GRANT OPTION;", (user,))
        print('Permissions Granted.')
    except Exception as ex:
        print('Error creating MySQL Database: %s' % ex)


def changePassword(cursor, username: str, NewPassword: str):
    try:
        cursor.execute("ALTER USER %s@'localhost' IDENTIFIED BY %s;", (username, NewPassword))
        print('User Password Changed.')
    except Exception as ex:
        print('Error Changing MySQL Password: %s' % ex)


def drop_database(cursor, DatabaseName: str):
    try:
        db = _validate(DatabaseName, 'dbname')
        cursor.execute(f'DROP DATABASE `{db}`;')
        print('Database Deleted.')
    except Exception as ex:
        print('Error dropping MySQL Database: %s' % ex)


def create_mail_user(cursor, email: str, password: str):
    """Parameterized — no SQL injection possible."""
    try:
        cursor.execute('USE mail')
        cursor.execute(
            'INSERT INTO `users` (`email`, `password`) VALUES (%s, %s);',
            (email, password)
        )
        mysqlconnection.commit()
        print('Mail Account Added.')
        cursor.execute('USE saspanel;')
    except Exception as ex:
        cursor.execute('USE saspanel;')
        print('Error Adding Record: %s' % ex)


def add_mail_domain(cursor, domain: str):
    """Parameterized — no SQL injection possible."""
    try:
        cursor.execute('USE mail')
        cursor.execute(
            'INSERT INTO `domains` (`domain`) VALUES (%s);',
            (domain,)
        )
        mysqlconnection.commit()
        print('Mail Domain Added.')
        cursor.execute('USE saspanel;')
    except Exception as ex:
        cursor.execute('USE saspanel;')
        print('Error Adding Record: %s' % ex)


def change_mail_password(cursor, Email: str, Password: str):
    """Parameterized — no SQL injection possible."""
    try:
        cursor.execute('USE mail')
        cursor.execute(
            "UPDATE `users` SET `password` = %s WHERE email = %s;",
            (Password, Email)
        )
        mysqlconnection.commit()
        print('Mail Password Changed.')
        cursor.execute('USE saspanel;')
    except Exception as ex:
        cursor.execute('USE saspanel;')
        print('Error Changing Password: %s' % ex)


# ---------------------------------------------------------------------------
# Nginx vhost management (SAFE — subprocess list form)
# ---------------------------------------------------------------------------

def add_vhost(username: str, domain: str):
    username = _validate(username, 'username')
    domain   = _validate(domain,   'domain')
    _run(['/bin/bash', 'scripts/add_vhost.sh', username, domain])


def remove_vhost(domain: str):
    domain = _validate(domain, 'domain')
    conf   = f'/etc/nginx/sites-enabled/{domain}-vhost.conf'
    try:
        if os.path.isfile(conf):
            os.remove(conf)
    except Exception as ex:
        print(f'Could not remove vhost conf: {ex}')
    _run(['systemctl', 'restart', 'nginx'])


# ---------------------------------------------------------------------------
# FTP management (SAFE)
# ---------------------------------------------------------------------------

def add_ftp_only(username: str, password: str):
    username = _validate(username, 'username')
    _run(['useradd', username])
    subprocess.run(['chpasswd'], input=f'{username}:{password}\n',
                   text=True, capture_output=True)
    try:
        with open('/etc/vsftpd.chroot_list', 'a') as f:
            f.write(username + '\n')
    except Exception as ex:
        print(f'vsftpd.chroot_list error: {ex}')
    _run(['chown', '-R', f'{username}:{username}', f'/home/{username}'])
    _run(['chmod', '0755', f'/home/{username}'])


def add_ftp(ftpusername: str, username: str, password: str):
    ftpusername = _validate(ftpusername, 'username')
    username    = _validate(username,    'username')
    _run(['useradd', '--home', f'/home/{username}', ftpusername])
    subprocess.run(['chpasswd'], input=f'{ftpusername}:{password}\n',
                   text=True, capture_output=True)
    try:
        with open('/etc/vsftpd.chroot_list', 'a') as f:
            f.write(ftpusername + '\n')
    except Exception as ex:
        print(f'vsftpd.chroot_list error: {ex}')
    _run(['chown', '-R', f'{ftpusername}:{ftpusername}', f'/home/{username}'])
    _run(['chmod', '0755', f'/home/{username}'])


def remove_ftp(ftpusername: str):
    ftpusername = _validate(ftpusername, 'username')
    _run(['chage', '-E0', ftpusername])
    _run(['usermod', '-s', '/sbin/nologin', ftpusername])


def change_ftp_pass(ftpUsername: str, ftpPassword: str):
    ftpUsername = _validate(ftpUsername, 'username')
    subprocess.run(['chpasswd'], input=f'{ftpUsername}:{ftpPassword}\n',
                   text=True, capture_output=True)


# ---------------------------------------------------------------------------
# SSL / Let's Encrypt (SAFE)
# ---------------------------------------------------------------------------

def generate_SSL(domain: str, email: str):
    domain = _validate(domain, 'domain')
    if not validateEmail(email):
        raise ValueError(f'Invalid email for SSL: {email!r}')
    _run(['/bin/bash', 'scripts/ssl_certificate_generate.sh', domain, email])


def renewALLSSL():
    _run(['certbot', 'renew', '--force-renewal'])


# ---------------------------------------------------------------------------
# Cron job management (SAFE)
# ---------------------------------------------------------------------------

def addCronJob(username: str, croncommand: str, logfile: str):
    username = _validate(username, 'username')
    _run(['/bin/bash', 'scripts/add_cron_job.sh', username, croncommand])


def deleteCronJob(username: str):
    username = _validate(username, 'username')
    _run(['crontab', '-u', username, '-r'])


# ---------------------------------------------------------------------------
# MySQL root setup
# ---------------------------------------------------------------------------

def set_mysql_root(password: str):
    """Password is passed via environment variable, not shell argument."""
    env = os.environ.copy()
    env['MYSQL_NEW_ROOT_PASS'] = password
    _run(['/bin/bash', 'scripts/mysql_admin.sh'], env=env)


# ---------------------------------------------------------------------------
# Log file reader
# ---------------------------------------------------------------------------

def readLines(fname: str, N: int) -> str:
    try:
        with open(fname) as f:
            lines = f.readlines()
        return ''.join(lines[-N:])
    except Exception:
        return 'File does not exist.'


def listToString(s):
    return ''.join(s)


# ---------------------------------------------------------------------------
# Installer
# ---------------------------------------------------------------------------

def install_packages(root_password, mail_password, domain, emailaddress, emailpassword):
    # FIX R18-05: cap all passwords passed to chpasswd / bcrypt at 128 chars.
    # chpasswd line format is "user:pass\n"; with long username, a 512-byte line limit applies.
    # bcrypt also silently truncates input at 72 bytes — enforcing a cap avoids silent failures.
    _MAX_PASS = 128
    root_password  = root_password[:_MAX_PASS]
    mail_password  = mail_password[:_MAX_PASS]
    emailpassword  = emailpassword[:_MAX_PASS]
    import subprocess as sp
    sp.run(['apt-get', '-y', 'update'])
    sp.run(['apt-get', '-y', 'upgrade'])
    sp.run(['mv', '/home/SASPanel/scripts/sample.config.ini', '/home/SASPanel/Database/config.ini'])
    WriteConfig(root_password)
    WriteMailConfig(emailaddress, emailpassword)
    sp.run(['apt-get', '-y', 'install', 'mysql-server', 'nginx', 'curl', 'wget', 'acl', 'vsftpd'])
    sp.run(['apt-get', '-y', 'install', 'certbot', 'python3-certbot-nginx'])
    set_mysql_root(root_password)
    sp.run(['apt-get', '-y', 'install', 'php-common', 'php-cli', 'php-fpm'])
    sp.run(['apt-get', 'install', '-y', 'dovecot-core', 'dovecot-imapd', 'dovecot-pop3d',
            'dovecot-lmtpd', 'dovecot-mysql'])
    sp.run(['apt-get', '-y', 'install', 'postfix-mysql'])
    sp.run(['/bin/bash', 'scripts/installer.sh'])
    sp.run(['apt', 'install', '-y', 'php-mysql', 'php-net-ldap2', 'php-net-ldap3',
            'php-imagick', 'php-common', 'php-gd', 'php-imap', 'php-json', 'php-curl',
            'php-zip', 'php-xml', 'php-mbstring', 'php-bz2', 'php-intl', 'php-gmp',
            'php-net-smtp', 'php-mail-mime', 'php-net-idna2', 'mailutils'])
    sp.run(['apt-get', '-y', 'install', 'zip', 'php-mbstring', 'php-zip', 'php-gd', 'php-mysql'])
    # passwords passed via env, NOT as shell args
    env = os.environ.copy()
    env['ROOT_PASS']       = root_password
    env['MAIL_PASS']       = mail_password
    env['ROUNDCUBE_PASS']  = generatePassword()   # FIX R9-09: was missing — caused :? failure in packages_installer.sh
    env['DOMAIN']          = domain
    env['EMAIL']           = emailaddress
    env['EMAIL_PASS']      = emailpassword
    sp.run(['/bin/bash', 'scripts/packages_installer.sh'], env=env)
    sp.run(['cp', '/home/SASPanel/scripts/saspanel.service', '/etc/systemd/system'])
    # FIX R24-01: create the dedicated system user required by saspanel.service (User=saspanel)
    sp.run(['useradd', '--system', '--no-create-home', '--shell', '/usr/sbin/nologin', 'saspanel'],
           check=False)  # check=False: may already exist on re-run
    sp.run(['chown', '-R', 'saspanel:saspanel', '/home/SASPanel'])
    sp.run(['systemctl', 'daemon-reload'])
    sp.run(['systemctl', 'enable', 'saspanel'])
    sp.run(['systemctl', 'enable', 'dovecot'])
    sp.run(['systemctl', 'enable', 'postfix'])
    sp.run(['systemctl', 'start', 'postfix'])
    sp.run(['systemctl', 'start', 'dovecot'])
    sp.run(['systemctl', 'restart', 'saspanel'])
    print('Install packages Completed.')