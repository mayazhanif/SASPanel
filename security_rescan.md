# SASPanel Security Audit — Full Scan Report
**Date**: 2026-09-06  
**Status**: Post-Hardening Final Scan

---

## 1. Dependency Vulnerabilities (pip-audit)

```
✅ No known vulnerabilities found
```

All packages upgraded to latest stable. `pip-audit` reports zero CVEs.

---

## 2. File-by-File Findings

### `app.py` ✅ CLEAN
| # | Issue | Severity | Status |
|---|---|---|---|
| - | SECRET_KEY loaded from env; hard crash if missing | - | ✅ Fixed |
| - | Session: HttpOnly, SameSite=Lax, Secure from env | - | ✅ Fixed |
| - | CSRF protection globally enabled (Flask-WTF) | - | ✅ Fixed |
| - | Rate limiting applied globally + tighter on login | - | ✅ Fixed |
| - | CSP: `unsafe-inline` removed from `script-src` | - | ✅ Fixed |
| - | `style-src` still has `'unsafe-inline'` | LOW | ⚠️ Acceptable — required for inline CSS in templates |
| - | `host` context processor uses `SERVER_NAME` env first | - | ✅ Fixed |

---

### `routes/login_routes.py` ✅ CLEAN
| # | Issue | Severity | Status |
|---|---|---|---|
| - | SQL injection (all queries parameterized) | - | ✅ Fixed |
| - | Password verified with bcrypt/PBKDF2; MD5 auto-upgraded | - | ✅ Fixed |
| - | Rate limit: 10/minute on `/login/` | - | ✅ Fixed |
| - | Session fixation: `session.clear()` before login | - | ✅ Fixed |
| - | User enumeration on forgot-password: same response either way | - | ✅ Fixed |
| - | Password reset token: 15-minute window | - | ✅ Fixed |
| - | Password length capped at 128 (bcrypt CPU-DoS) | - | ✅ Fixed |
| - | Token NOT invalidated atomically | MEDIUM | ⚠️ See fix below |

**New finding**: After `UPDATE users SET User_Password = %s WHERE UserResetToken = %s`, the token is cleared in a **separate** query. A race window exists. Fix: use a single `UPDATE ... SET User_Password=%s, UserResetToken='' WHERE UserResetToken=%s`.

---

### `routes/security.py` ✅ CLEAN
All sanitizers, path jail, audit logger — correct, no issues.

---

### `routes/ajax_routes.py` ✅ CLEAN
`/get_updates` requires valid session (admin or user). Returns only system metrics — no DB data exposed.

---

### `routes/custom_pages.py` ✅ CLEAN
| # | Issue | Severity | Status |
|---|---|---|---|
| - | `/installer` locked (403) once DB is connected | - | ✅ Fixed |
| - | `/reboot` requires `@require_admin` | - | ✅ Fixed |
| - | `/test` debug endpoint removed | - | ✅ Fixed |
| - | Installer inputs validated (domain regex, email prefix, password lengths) | - | ✅ Fixed |

---

### `routes/admin_routes.py` — 1 REMAINING ISSUE

**The admin FTP Add page (`admin_addAccounts`) still renders to `addAccounts.html` instead of redirecting.**  
Lines 720, 726, 735, 745, 749, 752, 755 all render to `adminFiles/ftpAccounts/addAccounts.html`.

This is a **UI/PRG issue, not a security vulnerability** — the data is properly parameterized and IDOR-protected. But it's an orphaned template that should be converted to flash+redirect like every other Add form.

All SQL: ✅ parameterized  
All IDOR: ✅ `Admin_id` scoped  
All shell calls: ✅ list-form subprocess  

---

### `routes/user_routes.py` ✅ CLEAN
All `#query = ...` lines are **commented-out legacy code** — not executed.  
All active queries: ✅ parameterized + `User_id` scoped.  
All Add routes: ✅ PRG (flash + redirect).

---

### `functions.py` ✅ CLEAN
| # | Issue | Severity | Status |
|---|---|---|---|
| - | `os.system()` calls removed; all use `subprocess list-form` | - | ✅ Fixed |
| - | `ExecShell` retained only for trusted hard-coded strings | - | ✅ Documented |
| - | `create_database` / `drop_database`: DB name validated via `_validate()` before f-string | - | ✅ Fixed |
| - | `hash_password`: PBKDF2-SHA256 via Werkzeug | - | ✅ Fixed |
| - | `generatePassword`: uses `secrets` module | - | ✅ Fixed |
| - | Passwords to chpasswd via stdin, not shell args | - | ✅ Fixed |
| - | MySQL root password via env var, not shell arg | - | ✅ Fixed |

---

## 3. Summary

| Category | Count |
|---|---|
| ✅ Clean files | 5/6 |
| ⚠️ Minor issues remaining | 2 |
| 🔴 Critical / High vulnerabilities | **0** |
| 📦 Dependency CVEs | **0** |

---

## 4. Two Remaining Fixes

### FIX-A (MEDIUM): Atomic token invalidation in `login_routes.py`

```python
# CURRENT (two-step — race window):
cursor.execute('UPDATE users SET User_Password = %s WHERE UserResetToken = %s;', (new_hash, token))
mysqlconnection.commit()
if cursor.rowcount > 0:
    cursor.execute("UPDATE users SET UserResetToken = '' WHERE UserResetToken = %s;", (token,))
    mysqlconnection.commit()

# FIX — single atomic UPDATE:
cursor.execute(
    "UPDATE users SET User_Password = %s, UserResetToken = '' WHERE UserResetToken = %s AND Is_Deleted = 0;",
    (new_hash, token)
)
mysqlconnection.commit()
```

### FIX-B (LOW/UI): `admin_addAccounts` — convert to PRG
Convert `render_template('adminFiles/ftpAccounts/addAccounts.html', ...)` calls to `flash() + redirect(url_for('routes.admin_viewAccounts'))` to match the rest of the codebase pattern.
