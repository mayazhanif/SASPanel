"""
ftp_server.py — SASPanel pyftpdlib FTP server

Replaces vsFTPd with a pure-Python FTP server backed by the SASPanel
database.  No OS user accounts are created; passwords are validated
directly against the ftp_accounts table.

Run as a separate systemd service:
    /home/SASPanel/venv/bin/python /home/SASPanel/ftp_server.py

Environment variables (loaded from .env via python-dotenv):
    FTP_HOST        — bind address              (default: 0.0.0.0)
    FTP_PORT        — command port              (default: 21)
    FTP_PASV_MIN    — passive port range start  (default: 40000)
    FTP_PASV_MAX    — passive port range end    (default: 40100)
    FTP_MASQ_ADDR   — public IP for PASV behind NAT (optional)
    FTP_MAX_CONS    — max simultaneous connections  (default: 100)
    FTP_MAX_PER_IP  — max connections per IP        (default: 5)
"""

import base64
import configparser
import logging
import os
import sys

from dotenv import load_dotenv

# ── Load environment ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

FTP_HOST   = os.getenv('FTP_HOST',     '0.0.0.0')
FTP_PORT   = int(os.getenv('FTP_PORT', '21'))
PASV_MIN   = int(os.getenv('FTP_PASV_MIN', '40000'))
PASV_MAX   = int(os.getenv('FTP_PASV_MAX', '40100'))
MASQ_ADDR  = os.getenv('FTP_MASQ_ADDR', None)
MAX_CONS   = int(os.getenv('FTP_MAX_CONS',   '100'))
MAX_PER_IP = int(os.getenv('FTP_MAX_PER_IP', '5'))

# ── Logging ─────────────────────────────────────────────────────────────────
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'ftp.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger('saspanel.ftp')


# ── Database helpers ─────────────────────────────────────────────────────────
def _get_db_config() -> dict:
    # RawConfigParser — avoids %(key)s interpolation which crashes on passwords
    # containing literal '%' (e.g. hrwLzcU8CT*KW%ui0eVfPI9q).
    cfg = configparser.RawConfigParser()
    cfg.read(os.path.join(BASE_DIR, 'Database', 'config.ini'))
    s = cfg['config']   # section is [config], not [database]
    return {
        'host':     s.get('host',     'localhost'),
        'port':     int(s.get('port', '3306')),
        'user':     s.get('user',     'root'),
        'password': s['password'],
        'database': s['database'],
    }


def _get_conn():
    import mysql.connector
    return mysql.connector.connect(**_get_db_config())


# ── pyftpdlib authorizer ─────────────────────────────────────────────────────
try:
    from pyftpdlib.authorizers import AuthenticationFailed
except ImportError:
    logger.critical('pyftpdlib not installed. Run: pip install pyftpdlib')
    sys.exit(1)


class SASPanelAuthorizer:
    """
    pyftpdlib abstract authorizer backed by SASPanel's ftp_accounts table.

    Passwords are stored as Base64 in the DB (matching Base64Encode /
    Base64Decode in functions.py).
    """

    ALL_PERMS = 'elradfmwMT'

    # ── internal ─────────────────────────────────────────────────────────────

    def _query_account(self, username: str):
        """Return (ftp_password_b64, serv_user) or None."""
        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute(
                '''
                SELECT fa.FTP_Password, u.servUser
                  FROM ftp_accounts fa
                  JOIN users u ON fa.User_id = u.User_id
                 WHERE fa.FTP_Username = %s
                   AND fa.Is_Active    = 1
                   AND u.Is_Deleted    = 0
                 LIMIT 1
                ''',
                (username,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row
        except Exception as exc:
            logger.error('[authorizer] DB error: %s', exc)
            return None

    @staticmethod
    def _encode(plain: str) -> str:
        return base64.b64encode(plain.encode()).decode()

    # ── pyftpdlib interface ───────────────────────────────────────────────────

    def validate_authentication(self, username: str, password: str, handler):
        row = self._query_account(username)
        if row is None:
            logger.warning('[auth] FAIL unknown user: %r from %s', username, handler.remote_ip)
            raise AuthenticationFailed('Invalid credentials.')
        stored_b64, _ = row
        if stored_b64 != self._encode(password):
            logger.warning('[auth] FAIL bad password: %r from %s', username, handler.remote_ip)
            raise AuthenticationFailed('Invalid credentials.')
        logger.info('[auth] OK: %r from %s', username, handler.remote_ip)

    def get_home_dir(self, username: str) -> str:
        row = self._query_account(username)
        home = f'/home/{row[1]}' if row else '/tmp'
        os.makedirs(home, exist_ok=True)
        return home

    def has_user(self, username: str) -> bool:
        return self._query_account(username) is not None

    def has_perm(self, username: str, perm: str, path=None) -> bool:
        return perm in self.ALL_PERMS

    def get_perms(self, username: str) -> str:
        return self.ALL_PERMS

    def get_msg_login(self, username: str) -> str:
        return f'Welcome {username}. SASPanel FTP service.'

    def get_msg_quit(self, username: str) -> str:
        return 'Goodbye.'

    def impersonate_user(self, username: str, password: str):
        """No-op — server runs as root, home dirs are pre-created."""

    def terminate_impersonation(self, username: str):
        """No-op."""


# ── Server entry point ────────────────────────────────────────────────────────
def main():
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers  import FTPServer

    handler = FTPHandler
    handler.authorizer         = SASPanelAuthorizer()
    handler.passive_ports      = range(PASV_MIN, PASV_MAX + 1)
    handler.banner             = 'SASPanel FTP service ready.'
    handler.max_login_attempts = 3
    handler.timeout            = 300

    if MASQ_ADDR:
        handler.masquerade_address = MASQ_ADDR

    server = FTPServer((FTP_HOST, FTP_PORT), handler)
    server.max_cons        = MAX_CONS
    server.max_cons_per_ip = MAX_PER_IP

    logger.info(
        'SASPanel FTP server starting — %s:%d  PASV %d-%d',
        FTP_HOST, FTP_PORT, PASV_MIN, PASV_MAX,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('FTP server stopped by user.')
    finally:
        server.close_all()


if __name__ == '__main__':
    main()
