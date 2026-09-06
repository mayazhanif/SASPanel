import base64
from flask import render_template, request, redirect, url_for, flash
from Database.DbConfig import mysqlconnection, mysql_connect
import hashlib
import json
from . import routes
from functions import *
from routes.security import (
    require_admin, log_security_event,
    sanitize_shell_arg, sanitize_cron_command,
    sanitize_log_filename, safe_log_path, sanitize_log_content,
)
from urllib.parse import urlparse
from flask import current_app
from datetime import datetime
from datetime import timedelta
from crontab import CronTab


def safe_referrer_redirect(fallback='routes.admin_dashboard'):
    """Redirect back to referrer ONLY if it's on the same host.
    Prevents open-redirect via a spoofed Referer header.
    Falls back to the admin dashboard if the referrer is absent or external.
    """
    referrer = request.referrer
    if referrer:
        ref_host = urlparse(referrer).netloc
        req_host = urlparse(request.url).netloc
        if ref_host == req_host:
            return redirect(referrer)
    return redirect(url_for(fallback))

@routes.route('/admin/dashboard')
def admin_dashboard():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/dashboard.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/users/viewUser')
def admin_viewUser():
    if check_admin_Login():
        mysqlconnection.reconnect()
        cursor = mysqlconnection.cursor()
        # FIX R14-01: info-leak — was showing ALL users from all admins
        cursor.execute(
            'SELECT * FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id '
            'WHERE Is_Deleted=0 AND users.Admin_id=%s;',
            (str(session['id']),)
        )
        userList = cursor.fetchall()
        # UI: also fetch packages for the embedded Add User tab
        cursor.execute('SELECT * FROM `packages` WHERE Is_Active=1 AND Admin_id=%s;', (str(session['id']),))
        results = cursor.fetchall()
        return render_template('adminFiles/users/viewUser.html', userList=userList, results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/users/deleteUser', methods =['GET', 'POST'])
def admin_deleteUser():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('userID'):
            userID=request.args.get('userID')
            mysqlconnection.reconnect()
            cursor = mysqlconnection.cursor()
            # FIX R14-02: IDOR — no Admin_id ownership check; any admin could delete any user
            cursor.execute(
                "UPDATE `users` SET `Is_Deleted` = '1' "
                "WHERE `users`.`User_id` =%s AND Admin_id=%s",
                (userID, str(session['id']))
            )
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('User Deleted.')
                return redirect(url_for("routes.admin_viewUser"))
            else:
                flash('User not Deleted.')
                return redirect(url_for("routes.admin_viewUser"))

        else:
            return redirect(url_for("routes.admin_viewUser"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIXED: parameterized queries (was raw string concatenation)
        cursor.execute('SELECT * FROM users WHERE Is_Deleted=0 AND Admin_id=%s', (session['id'],))
        cursor.fetchall()
        totalUsers = str(cursor.rowcount)
        cursor.execute('SELECT Reg_Date FROM administrator WHERE Admin_id=%s', (session['id'],))
        details = cursor.fetchone()
        regDate = str(details[0]) if details else ''
        cursor.execute('SELECT * FROM `packages` WHERE Is_Active=1 AND Admin_id=%s', (session['id'],))
        cursor.fetchall()
        totalPackages = str(cursor.rowcount)

        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            # FIX R6-01: cap Name length to prevent DoS / DB truncation
            if not Name or len(Name) > 128:
                return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages, msg={'error': 'danger', 'message': 'Name must be 1-128 characters.'})
            cursor.execute('UPDATE `administrator` SET `Admin_Name` = %s WHERE Admin_id = %s;', (Name, session['id']))
            mysqlconnection.commit()
            if cursor.rowcount > 0:
                session['Name'] = Name
                return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages, msg={'error': 'success', 'message': 'Name Updated Successfully.'})
            else:
                return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages, msg={'error': 'primary', 'message': 'Name not Updated.'})
        elif request.method == 'POST' and 'pass1' in request.form and 'pass2' in request.form:
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            # FIX R18-03: enforce password length before bcrypt (prevents DoS via huge input
            # and ensures a minimum password strength; bcrypt silently truncates at 72 bytes)
            if len(pass1) < 8 or len(pass1) > 128:
                return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages,
                                       passmsg={'error': 'danger', 'message': 'Password must be between 8 and 128 characters.'})
            if pass1 == pass2:
                cursor = mysqlconnection.cursor()
                # FIXED: use bcrypt instead of MD5
                securePassword = hash_password(pass1)
                cursor.execute('UPDATE `administrator` SET `Admin_Password` = %s WHERE Admin_id = %s;', (securePassword, session['id']))
                mysqlconnection.commit()
                if cursor.rowcount > 0:
                    return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages, passmsg={'error': 'success', 'message': 'Password Updated Successfully.'})
                else:
                    return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages, passmsg={'error': 'primary', 'message': 'Password not Updated.'})
            else:
                return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages,
                                       passmsg={'error': 'danger', 'message': 'Password and Confirm Password Mismatch.'})
        else:
            return render_template('adminFiles/profile.html', users=totalUsers, regDate=regDate, totalPackages=totalPackages)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/users/adduser', methods=['GET', 'POST'])
def admin_addUser():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R15-05: info-leak — package dropdown showed ALL admins' packages
        cursor.execute('SELECT * FROM `packages` WHERE Is_Active=1 AND Admin_id=%s;', (str(session['id']),))
        results = cursor.fetchall()
        if request.method == 'POST' and 'Name' in request.form and 'Email' in request.form and 'pass1' in request.form and 'pass2' in request.form and 'packageID' in request.form:
            User_Name = request.form['Name']
            Admin_id = str(session['id'])
            User_email = request.form['Email']
            User_Password = request.form['pass1']
            Confirm_Password = request.form['pass2']
            # FIX R6-02: validate email format + cap name length before INSERT
            from functions import validateEmail
            if not validateEmail(User_email):
                flash('Invalid email address.')
                return redirect(url_for('routes.admin_viewUser'))
            if not User_Name or len(User_Name) > 128:
                flash('Name must be 1-128 characters.')
                return redirect(url_for('routes.admin_viewUser'))
            if User_Password == Confirm_Password:
                # FIX R19-01: enforce password length before bcrypt to prevent DoS
                if len(User_Password) < 8 or len(User_Password) > 128:
                    flash('Password must be between 8 and 128 characters.')
                    return redirect(url_for('routes.admin_viewUser'))
                # FIXED: bcrypt instead of MD5 (VULN-addUser)
                securePassword = hash_password(User_Password)
                packageID = request.form['packageID']
                servUser = generateservUser(User_Name, User_email)
                cursor = mysqlconnection.cursor()
                cursor.execute("INSERT INTO `users` (`User_id`, `servUser`, `User_email`, `User_Password`, `User_Name`, `UserResetToken`, `Token_Expiry`, `Admin_id`, `Package_id`, `Is_Deleted`, `User_Reg_Date`) VALUES (NULL, %s, %s, %s, %s, '', CURRENT_TIMESTAMP, %s, %s, '0', CURRENT_TIMESTAMP);", (servUser, User_email, securePassword, User_Name, Admin_id, packageID))
                userID = str(cursor.lastrowid)
                mysqlconnection.commit()
                if cursor.rowcount > 0:
                    add_default_user(servUser, User_Password)
                    dbUser = generateservUser(User_Name, User_email)
                    dbPassword = generatePassword()
                    base64dbPassword = Base64Encode(dbPassword)
                    try:
                        cursor.execute("INSERT INTO `mysqldbusers` (`DbUser_ID`, `DbUsername`, `DbPassword`, `User_id`, `Is_Active`) VALUES (NULL, %s, %s, %s, '1')",(dbUser,base64dbPassword,userID))
                        mysqlconnection.commit()
                        createUser(cursor,dbUser,dbPassword)
                    except:
                        flash('Email already exists.')
                        return redirect(url_for('routes.admin_viewUser'))
                    flash(f'User {User_email} added. DB user: {dbUser} | DB pass: {dbPassword}')
                    return redirect(url_for('routes.admin_viewUser'))
                else:
                    flash('User not created. Fill all fields correctly.')
                    return redirect(url_for('routes.admin_viewUser'))
            else:
                flash('Password and Confirm Password do not match.')
                return redirect(url_for('routes.admin_viewUser'))
        else:
            return redirect(url_for('routes.admin_viewUser'))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/users/updateUser', methods =['GET', 'POST'])
def admin_updateUser():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('userID'):
            userID=request.args.get('userID')
            cursor = mysqlconnection.cursor()
            # FIX R15-06: info-leak — package dropdown showed ALL admins' packages in update form
            cursor.execute('SELECT * FROM `packages` WHERE Is_Active=1 AND Admin_id=%s;', (str(session['id']),))
            results = cursor.fetchall()
            # FIX R14-03: IDOR — no Admin_id scope on GET fetch; any admin could view any user's data
            cursor.execute(
                "SELECT * FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id "
                "WHERE Is_Deleted=0 AND User_id=%s AND users.Admin_id=%s",
                (userID, str(session['id']))
            )
            user = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('adminFiles/users/updateUser.html', user=user, results=results)
            else:
                return redirect(url_for("routes.admin_viewUser"))
            #return redirect(url_for('routes.login'))
        elif request.method == 'POST' and 'userID' in request.form and 'Name' in request.form and 'Email' in request.form and 'password' in request.form  and 'packageID' in request.form:
            print("TEST")
            packageID = request.form['packageID']
            userID = request.form['userID']
            Name = request.form['Name']
            Email = request.form['Email']
            password = request.form['password']
            # FIX R6-03: validate email + cap name length on update
            from functions import validateEmail
            if not validateEmail(Email):
                flash('Invalid email address.')
                return safe_referrer_redirect()
            if not Name or len(Name) > 128:
                flash('Name must be 1-128 characters.')
                return safe_referrer_redirect()
            # FIX R19-02: enforce password length before bcrypt to prevent DoS
            if len(password) < 8 or len(password) > 128:
                flash('Password must be between 8 and 128 characters.')
                return safe_referrer_redirect()
            # FIXED: bcrypt instead of MD5 (VULN-updateUser)
            securePassword = hash_password(password)
            cursor = mysqlconnection.cursor()
            cursor.execute("UPDATE `users` SET `Package_Id` = %s, `User_email` = %s, `User_Password` = %s, `User_Name` = %s WHERE `users`.`User_id` = %s AND Admin_id = %s", (packageID, Email, securePassword, Name, userID, session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('User Updated.')
                return safe_referrer_redirect()
            else:
                flash('User Not Updated.')
                return safe_referrer_redirect()
        else:
            return safe_referrer_redirect()

    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Packages/addPackage' , methods=['GET', 'POST'])
def admin_addPackage():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'POST' and 'packagename' in request.form and 'domains' in request.form and 'dbs' in request.form and 'subdomains' in request.form and 'ftps' in request.form and 'mails' in request.form and 'storage' in request.form:
            Package_Name = request.form['packagename']
            Admin_id = str(session['id'])
            # FIX R22-03: validate all limit fields are non-negative integers
            # Non-integer values cause a MySQL type error visible to the user;
            # negative values allow bypassing resource limits.
            def _to_nonneg_int(val, label, max_val=9999):
                try:
                    v = int(val)
                except (ValueError, TypeError):
                    raise ValueError(f'{label} must be a whole number.')
                if v < 0:
                    raise ValueError(f'{label} must be 0 or greater.')
                if v > max_val:
                    raise ValueError(f'{label} must be {max_val} or less.')
                return v
            try:
                Limit_Domains  = _to_nonneg_int(request.form['domains'],    'Domain limit')
                Limit_DB       = _to_nonneg_int(request.form['dbs'],        'DB limit')
                Limit_FTP      = _to_nonneg_int(request.form['ftps'],       'FTP limit')
                Limit_Mails    = _to_nonneg_int(request.form['mails'],      'Mail limit')
                Sub_Domains    = _to_nonneg_int(request.form['subdomains'], 'Subdomain limit')
                Storage_Limit  = _to_nonneg_int(request.form['storage'],    'Storage limit', max_val=999999)
            except ValueError as e:
                return render_template('adminFiles/Packages/viewPackages.html',
                                       msg={'error': 'danger', 'message': str(e)}, packages=[])
            if not Package_Name or len(Package_Name) > 128:
                return render_template('adminFiles/Packages/viewPackages.html',
                                       msg={'error': 'danger', 'message': 'Package name must be 1-128 characters.'}, packages=[])
            CGI_ACCESS='0'
            if request.form.get("cgiAccess"):
                CGI_ACCESS = '1'
            cursor = mysqlconnection.cursor()
            cursor.execute("INSERT INTO `packages` (`Package_Id`, `Package_Name`, `Admin_id`, `Limit_FTP`, `Limit_Mails`, `Limit_Domains`, `CGI_ACCESS`, `Limit_DB`, `Sub_Domains`, `Storage_Limit`) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                           (Package_Name, Admin_id, Limit_FTP, Limit_Mails, Limit_Domains, CGI_ACCESS, Limit_DB, Sub_Domains, Storage_Limit))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('Package created successfully.')
                return redirect(url_for('routes.admin_viewPackages'))
            else:
                return render_template('adminFiles/Packages/viewPackages.html',
                                       msg={'error': 'primary', 'message': 'Package not created. Fill all fields correctly.'}, packages=[])

        else:
            return redirect(url_for('routes.admin_viewPackages'))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Packages/viewPackages')
def admin_viewPackages():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R14-04: info-leak — was showing ALL packages from all admins
        cursor.execute('SELECT * FROM `packages` WHERE Is_Active=1 AND Admin_id=%s;', (str(session['id']),))
        packages = cursor.fetchall()
        return render_template('adminFiles/Packages/viewPackages.html', packages=packages)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Packages/updatePackage', methods =['GET', 'POST'])
def admin_updatePackage():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('packageID'):
            packageID=request.args.get('packageID')
            cursor = mysqlconnection.cursor()
            # FIX R14-05: IDOR — no Admin_id scope; any admin could view any package
            cursor.execute('SELECT * FROM `packages` WHERE Package_Id=%s AND Admin_id=%s', (packageID, str(session['id'])))
            package = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('adminFiles/Packages/updatePackage.html', package=package)
            else:
                return redirect(url_for("routes.admin_viewPackages"))
            #return redirect(url_for('routes.login'))
        elif request.method == 'POST' and 'packageID' in request.form and 'packagename' in request.form and 'domains' in request.form and 'dbs' in request.form and 'subdomains' in request.form and 'ftps' in request.form and 'mails' in request.form and 'storage' in request.form:
            packageID = request.form['packageID']
            Package_Name = request.form['packagename']
            Admin_id = str(session['id'])
            # FIX R22-04: validate all limit fields are non-negative integers
            def _to_nonneg_int(val, label, max_val=9999):
                try:
                    v = int(val)
                except (ValueError, TypeError):
                    raise ValueError(f'{label} must be a whole number.')
                if v < 0:
                    raise ValueError(f'{label} must be 0 or greater.')
                if v > max_val:
                    raise ValueError(f'{label} must be {max_val} or less.')
                return v
            try:
                Limit_Domains  = _to_nonneg_int(request.form['domains'],    'Domain limit')
                Limit_DB       = _to_nonneg_int(request.form['dbs'],        'DB limit')
                Limit_FTP      = _to_nonneg_int(request.form['ftps'],       'FTP limit')
                Limit_Mails    = _to_nonneg_int(request.form['mails'],      'Mail limit')
                Sub_Domains    = _to_nonneg_int(request.form['subdomains'], 'Subdomain limit')
                Storage_Limit  = _to_nonneg_int(request.form['storage'],    'Storage limit', max_val=999999)
            except ValueError as e:
                flash(str(e))
                return safe_referrer_redirect()
            if not Package_Name or len(Package_Name) > 128:
                flash('Package name must be 1-128 characters.')
                return safe_referrer_redirect()
            CGI_ACCESS='0'
            if request.form.get("cgiAccess"):
                CGI_ACCESS = '1'
            cursor = mysqlconnection.cursor()
            # FIX IDOR-P2: include Admin_id in UPDATE to prevent cross-admin package modification
            cursor.execute("UPDATE `packages` SET `Package_Name` = %s, `Limit_FTP` = %s, `Limit_Mails` = %s, `Limit_Domains` = %s, `CGI_ACCESS` = %s, `Limit_DB` = %s, `Sub_Domains` = %s, `Storage_Limit` = %s WHERE `packages`.`Package_Id` = %s AND `Admin_id` = %s",
                           (Package_Name, Limit_FTP, Limit_Mails, Limit_Domains, CGI_ACCESS, Limit_DB, Sub_Domains, Storage_Limit, packageID, Admin_id))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('Hosting Package Updated.')
                return safe_referrer_redirect()
            else:
                flash('Hosting Package Not Updated.')
                return safe_referrer_redirect()
        else:
            return safe_referrer_redirect()

    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Packages/deletePackage', methods =['GET', 'POST'])
def admin_deletePackage():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('packageID'):
            packageID=request.args.get('packageID')
            cursor = mysqlconnection.cursor()
            # FIX IDOR-P1: only delete packages belonging to this admin
            cursor.execute("UPDATE `packages` SET `Is_Active` = '0' WHERE `packages`.`Package_Id` =%s AND `Admin_id`=%s",(packageID, str(session['id'])))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('Hosting Package Deleted.')
                return redirect(url_for("routes.admin_viewPackages"))
            else:
                flash('Hosting Package Not Deleted.')
                return redirect(url_for("routes.admin_viewPackages"))
        else:
            return redirect(url_for("routes.admin_viewPackages"))
    else:
        return redirect(url_for('routes.login'))
@routes.route('/admin/domains/addDomain', methods = ['GET', 'POST'])
def admin_addDomain():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R10-05: info-leak — was showing ALL users from all admins in dropdown
        cursor.execute('SELECT * FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;', (str(session['id']),))
        users = cursor.fetchall()
        if request.method == 'POST' and 'userID' in request.form and 'DomainName' in request.form:
            userID = request.form['userID']
            if userID == '':
                msg={"error":"danger", "message": "User not Selected."}
                return render_template('adminFiles/domains/viewDomains.html', users=users, msg=msg, results=[])
            # FIX R9-03: IDOR — verify userID belongs to this admin before adding domain
            cursor.execute('SELECT servUser,User_email FROM `users` where Is_Deleted=0 and User_id=%s AND Admin_id=%s;',(userID, str(session['id'])))
            user = cursor.fetchone()
            if user is None:
                msg={"error":"danger", "message": "User not found or access denied."}
                return render_template('adminFiles/domains/viewDomains.html', users=users, msg=msg, results=[])
            getUserName = user[0]
            getEmail = user[1]
            DomainName = request.form['DomainName']
            # FIX R7-03: validate DomainName before passing to add_vhost/generate_SSL (shell scripts)
            try:
                DomainName = sanitize_shell_arg(DomainName, 'domain')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid domain name. Use only letters, digits, dots, hyphens.'}
                return render_template('adminFiles/domains/viewDomains.html', users=users, msg=msg, results=[])
            try:
                cursor.execute("INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, %s, %s, '0', '0');",(DomainName,userID))
                mysqlconnection.commit()
            except:
                msg={"error":"danger","message":"Domain Already Added."}
                return render_template('adminFiles/domains/viewDomains.html', users=users, msg=msg, results=[])
            if cursor.rowcount>0:
                DomainID = str(cursor.lastrowid)
                add_vhost(getUserName,DomainName)
                generate_SSL(DomainName,getEmail)
                ExpiryDate = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
                privkey ="/etc/letsencrypt/live/"+DomainName+"/privkey.pem"
                fullchain="/etc/letsencrypt/live/"+DomainName+"/fullchain.pem"
                cursor.execute("INSERT INTO `sslcertificates` (`Cert_ID`, `Domain_Id`, `User_id`, `Certificate`, `PrivateKey`, `ExpiryDate`, `Is_Active`) VALUES (NULL, %s, %s, %s, %s, %s, '1');",(DomainID,userID,fullchain,privkey,ExpiryDate))
                mysqlconnection.commit()
                add_mail_domain(cursor, DomainName)

                # ── Optional: auto-create FTP account ──────────────────────
                if request.form.get('createFTP'):
                    import secrets as _sec
                    ftp_pass = _sec.token_urlsafe(12)
                    ftp_user = getUserName  # use the server username as FTP username
                    ftp_enc  = Base64Encode(ftp_pass)
                    ftp_dir  = f'/home/{getUserName}/public_html'
                    try:
                        cursor.execute(
                            "INSERT INTO `ftp_accounts` "
                            "(`Account_Id`,`User_id`,`Directory`,`FTP_Username`,`FTP_Password`,`Is_Active`) "
                            "VALUES (NULL,%s,%s,%s,%s,'1')",
                            (userID, ftp_dir, ftp_user, ftp_enc)
                        )
                        mysqlconnection.commit()
                        add_ftp(ftp_user, getUserName, ftp_pass)
                    except Exception:
                        pass  # FTP account may already exist — not fatal

                # ── Optional: auto-create info@ mail account ────────────────
                if request.form.get('createMail'):
                    import secrets as _sec2
                    mail_pass  = _sec2.token_urlsafe(12)
                    mail_addr  = 'info@' + DomainName
                    mail_enc   = Base64Encode(mail_pass)
                    try:
                        cursor.execute(
                            "INSERT INTO `mail_accounts` "
                            "(`Mail_Id`,`Domain_Id`,`User_id`,`Mail_Address`,`Mail_Pass`,`Is_Active`) "
                            "VALUES (NULL,%s,%s,%s,%s,'1')",
                            (DomainID, userID, mail_addr, mail_enc)
                        )
                        mysqlconnection.commit()
                        create_mail_user(cursor, mail_addr, mail_pass)
                    except Exception:
                        pass  # Mail account may already exist — not fatal

                flash('Domain added successfully.')
                return redirect(url_for('routes.admin_viewDomains'))
            else:
                msg = {"error": "danger", "message": "Domain Not Added."}
                return render_template('adminFiles/domains/viewDomains.html', users=users, msg=msg, results=[])
        else:
            return redirect(url_for('routes.admin_viewDomains'))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domains/renewSSL')
def admin_renewSSL():
    mysqlconnection.reconnect()
    if check_admin_Login():
        renewALLSSL()
        flash('SSL Certificates Renewed.')
        return redirect(url_for('routes.admin_viewDomains'))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domains/viewDomains')
def admin_viewDomains():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R15-04: info-leak — was showing ALL domains from all admins
        cursor.execute(
            'SELECT * FROM domains '
            'JOIN users ON domains.User_id = users.User_id '
            'JOIN sslcertificates ON sslcertificates.Domain_Id = domains.Domain_Id '
            'WHERE users.Admin_id=%s;',
            (str(session['id']),)
        )
        results = cursor.fetchall()
        # UI: also fetch users list so the embedded Add Domain form can populate its dropdown
        cursor.execute('SELECT * FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;', (str(session['id']),))
        users = cursor.fetchall()
        return render_template('adminFiles/domains/viewDomains.html', results=results, users=users)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domains/updateDomains')
def admin_updateDomains():
    mysqlconnection.reconnect()
    if check_admin_Login():
        msg=''
        if request.method == 'GET' and request.args.get('domainID'):
            domainID=request.args.get('domainID')
            cursor = mysqlconnection.cursor()
            # FIX R9-02: IDOR — no Admin_id ownership check before suspend/unsuspend
            cursor.execute(
                "SELECT `Domain_Suspended` FROM domains "
                "WHERE `domains`.`Domain_Id` =%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (domainID, str(session['id']))
            )
            domain = cursor.fetchone()
            if domain is None:
                flash('Domain not found or access denied.')
                return redirect(url_for('routes.admin_viewDomains'))
            if domain[0]==0:
                cursor.execute("UPDATE `domains` SET `Domain_Suspended` = '1' WHERE `domains`.`Domain_Id` =%s AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",(domainID, str(session['id'])))
                mysqlconnection.commit()
                flash('Domain Suspended.')
                return redirect(url_for("routes.admin_viewDomains"))
            else:
                cursor.execute("UPDATE `domains` SET `Domain_Suspended` = '0' WHERE `domains`.`Domain_Id` =%s AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",(domainID, str(session['id'])))
                mysqlconnection.commit()
                flash('Domain not Suspended.')
                return redirect(url_for("routes.admin_viewDomains"))
        return redirect(url_for("routes.admin_viewDomains"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domain/deleteDomain', methods =['GET', 'POST'])
def admin_deleteDomain():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('domainID'):
            domainID=request.args.get('domainID')
            cursor = mysqlconnection.cursor()
            cursor.execute(
                'SELECT Domain_Name FROM `domains` '
                'WHERE Is_Deleted=0 AND Domain_Id=%s '
                'AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)',
                (domainID, str(session['id']))
            )
            row = cursor.fetchone()
            # FIX R7-04: null-pointer crash + no Admin_id ownership check on domain delete
            if row is None:
                flash('Domain not found or access denied.')
                return redirect(url_for('routes.admin_viewDomains'))
            DomainName = row[0]
            # Scope deletion to domains belonging to this admin's users
            cursor.execute(
                "UPDATE `domains` SET `Is_Deleted` = '1' "
                "WHERE `domains`.`Domain_Id` =%s "
                "AND `User_id` IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (domainID, str(session['id']))
            )
            mysqlconnection.commit()
            if cursor.rowcount>0:
                remove_vhost(DomainName)
                return redirect(url_for("routes.admin_viewDomains"))
            else:
                return redirect(url_for("routes.admin_viewDomains"))

        else:
            return redirect(url_for("routes.admin_viewDomains"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Databases/addDB', methods = ['GET','POST'])
def admin_addDB():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R10-04: info-leak — was showing ALL users from all admins in dropdown
        cursor.execute('SELECT * FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;', (str(session['id']),))
        users = cursor.fetchall()
        if request.method == 'POST' and 'userID' in request.form and 'databaseName' in request.form:
            userID = request.form['userID']
            if(userID==""):
                msg={"error":"danger", "message": "User not Selected."}
                return render_template('adminFiles/MysqlDatabase/viewDatabases.html', users=users, msg=msg, results=[])
            # FIX R9-04: IDOR — verify userID belongs to this admin before adding database
            cursor.execute('SELECT * FROM `mysqldbusers` INNER JOIN users ON mysqldbusers.User_id = users.User_id where Is_Deleted=0 and users.User_id= %s AND users.Admin_id=%s;',(userID, str(session['id'])))
            DBUserbyID = cursor.fetchone()
            if DBUserbyID is None:
                msg={"error":"danger", "message": "User not found or access denied."}
                return render_template('adminFiles/MysqlDatabase/viewDatabases.html', users=users, msg=msg, results=[])

            databaseName = request.form['databaseName']
            try:
                cursor.execute("INSERT INTO `msqldatabases` (`DB_ID`, `DbName`, `User_id`, `DbUser_ID`, `Is_Active`) VALUES (NULL, %s, %s, %s, '1');",(databaseName,userID,str(DBUserbyID[0])))
                mysqlconnection.commit()
            except:
                msg={"error":"danger","message":"Database name already in use."}
                return render_template('adminFiles/MysqlDatabase/viewDatabases.html', users=users, msg=msg, results=[])
            if cursor.rowcount>0:
                create_database(cursor,databaseName,DBUserbyID[1])
                flash('Database created successfully.')
                return redirect(url_for('routes.admin_viewDatabases'))
            else:
                msg = {"error": "danger", "message": "Database Adding not Successfull."}
                return render_template('adminFiles/MysqlDatabase/viewDatabases.html', users=users, msg=msg, results=[])
        else:
            return redirect(url_for('routes.admin_viewDatabases'))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Databases/viewDatabases')
def admin_viewDatabases():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R14-06: info-leak — was showing ALL databases from all admins
        cursor.execute(
            'SELECT * FROM mysqldbusers '
            'LEFT JOIN msqldatabases ON msqldatabases.DbUser_ID = mysqldbusers.DbUser_ID '
            'LEFT JOIN users ON users.User_id = mysqldbusers.User_id '
            'WHERE msqldatabases.Is_Active = 1 AND users.Admin_id=%s',
            (str(session['id']),)
        )
        results = cursor.fetchall()
        # UI: fetch users for the embedded Add Database tab
        cursor.execute('SELECT * FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;', (str(session['id']),))
        users = cursor.fetchall()
        return render_template('adminFiles/MysqlDatabase/viewDatabases.html', results=results, users=users)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Databases/deleteDatabase', methods =['GET', 'POST'])
def admin_deleteDatabase():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('DbID'):
            DbID=request.args.get('DbID')
            cursor = mysqlconnection.cursor()
            # FIX R19-06: scope SELECT to this admin's DBs to prevent info-leak via timing
            cursor.execute(
                'SELECT DbName FROM `msqldatabases` '
                'WHERE DB_ID=%s AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)',
                (DbID, str(session['id']))
            )
            getDBName = cursor.fetchone()
            if getDBName is None:
                flash('Database not found or access denied.')
                return redirect(url_for("routes.admin_viewDatabases"))
            getDBName = getDBName[0]
            # FIX IDOR-D1: verify the DB belongs to a user owned by this admin
            cursor.execute("UPDATE `msqldatabases` SET `Is_Active` = '0' WHERE `msqldatabases`.`DB_ID` = %s AND `User_id` IN (SELECT User_id FROM users WHERE Admin_id=%s)",(DbID, str(session['id'])))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                drop_database(cursor,getDBName)
                flash('Database Dropped.')
                return redirect(url_for("routes.admin_viewDatabases"))
            else:
                flash('Database not Dropped.')
                return redirect(url_for("routes.admin_viewDatabases"))

        else:
            return redirect(url_for("routes.admin_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))



@routes.route('/admin/Databases/updateDBPass', methods=['GET', 'POST'])
def admin_updateDBPass():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        msg = ''
        if request.method == 'GET' and request.args.get('DbID'):
            DbUser_ID = request.args.get('DbID')
            # FIX R9-05: IDOR - scope DB password view to admin's own users
            cursor.execute(
                "SELECT * FROM `mysqldbusers` "
                "WHERE `mysqldbusers`.`DbUser_ID` =%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (DbUser_ID, str(session['id']))
            )
            database = cursor.fetchone()
            if database is None:
                flash('Database not found or access denied.')
                return redirect(url_for('routes.admin_viewDatabases'))
            # FIX: was missing return — caused None response
            return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, db=database, msg=msg)
        elif request.method == 'POST' and 'DbID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            DbUser_ID = request.form['DbID']
            # FIX R11-02: IDOR - POST branch validates Admin_id ownership
            cursor.execute(
                "SELECT DbUsername FROM `mysqldbusers` "
                "WHERE `mysqldbusers`.`DbUser_ID` =%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (DbUser_ID, str(session['id']))
            )
            row = cursor.fetchone()
            if row is None:
                flash('Database not found or access denied.')
                return redirect(url_for('routes.admin_viewDatabases'))
            mysqlUsername = row[0]
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                # FIX R21-04: cap DB password length
                if len(pass1) < 1 or len(pass1) > 128:
                    msg = {'error': 'danger', 'message': 'Password must be between 1 and 128 characters.'}
                    return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, db=None, msg=msg)
                EncodedPassword = Base64Encode(pass1)
                cursor.execute(
                    "UPDATE `mysqldbusers` SET `DbPassword` =%s WHERE `mysqldbusers`.`DbUser_ID` = %s",
                    (EncodedPassword, DbUser_ID)
                )
                mysqlconnection.commit()
                if cursor.rowcount > 0:
                    changePassword(cursor, mysqlUsername, pass1)
                    msg = {'error': 'success', 'message': 'Database password updated successfully.'}
                    return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, db=None, msg=msg)
                else:
                    msg = {'error': 'danger', 'message': 'Password not updated.'}
                    return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, db=None, msg=msg)
            else:
                msg = {'error': 'danger', 'message': 'Passwords do not match.'}
                return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, db=None, msg=msg)
        else:
            return redirect(url_for('routes.admin_viewDatabases'))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/addAccounts', methods=['GET', 'POST'])
def admin_addAccounts():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'userID' in request.form and 'ftpUsername' in request.form and 'ftpPassword' in request.form:
            userID = request.form['userID']
            if(userID==""):
                flash('User not selected.')
                return redirect(url_for('routes.admin_viewAccounts'))
            # FIX D-09: IDOR — verify userID belongs to this admin before adding FTP account
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s AND Admin_id=%s',(userID, str(session['id'])))
            row = cursor.fetchone()
            if row is None:
                flash('User not found or access denied.')
                return redirect(url_for('routes.admin_viewAccounts'))
            getUserName = row[0]
            ftpUsername = request.form['ftpUsername']
            ftpPassword = request.form['ftpPassword']
            # FIX R7-01: validate ftpUsername — it becomes a Linux OS username
            try:
                ftpUsername = sanitize_shell_arg(ftpUsername, 'username')
            except ValueError:
                flash('Invalid FTP username. Lowercase letters, digits, hyphens, underscores only.')
                return redirect(url_for('routes.admin_viewAccounts'))
            encodedPass = Base64Encode(ftpPassword)
            Directory = f"/home/{getUserName}/public_html"
            try:
                cursor.execute("INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES (NULL,%s,%s,%s,%s, '1');", (userID,Directory,ftpUsername,encodedPass))
                mysqlconnection.commit()
            except:
                flash('FTP username already in use.')
                return redirect(url_for('routes.admin_viewAccounts'))
            if cursor.rowcount>0:
                add_ftp(ftpUsername,getUserName,ftpPassword)
                flash('FTP account added successfully.')
                return redirect(url_for('routes.admin_viewAccounts'))
            else:
                flash('FTP account not added.')
                return redirect(url_for('routes.admin_viewAccounts'))
        else:
            return redirect(url_for('routes.admin_viewAccounts'))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/viewAccounts')
def admin_viewAccounts():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R14-07: info-leak — was showing ALL FTP accounts from all admins
        cursor.execute(
            'SELECT * FROM `ftp_accounts` INNER JOIN users ON ftp_accounts.User_id = users.User_id '
            'WHERE ftp_accounts.Is_Active=1 AND users.Admin_id=%s;',
            (str(session['id']),)
        )
        results = cursor.fetchall()
        # Also fetch users list for the 'Add FTP Account' form dropdown
        cursor.execute(
            'SELECT User_id, User_Name, User_email FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;',
            (str(session['id']),)
        )
        users = cursor.fetchall()
        msg = ''
        return render_template('adminFiles/ftpAccounts/viewAccounts.html', results=results, users=users)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/FTPAccounts/updateAccountPass', methods=['GET', 'POST'])
def admin_updateAccountPass():
    mysqlconnection.reconnect()
    if check_admin_Login():
        msg=''
        cursor = mysqlconnection.cursor()
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')
            # FIX R11-03: IDOR — no Admin_id ownership check on GET update form
            cursor.execute(
                "SELECT * FROM `ftp_accounts` "
                "INNER JOIN users ON ftp_accounts.User_id = users.User_id "
                "WHERE ftp_accounts.Account_Id=%s AND users.Admin_id=%s",
                (AccID, str(session['id']))
            )
            account = cursor.fetchone()
            if account is not None:
                return render_template('adminFiles/ftpAccounts/updateAccountPass.html', account=account[0])
            else:
                return redirect(url_for("routes.admin_viewAccounts"))
        elif request.method == 'POST' and 'AccID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            AccID = request.form['AccID']
            # FIX IDOR-F1: verify FTP account belongs to a user under this admin
            cursor.execute('SELECT FTP_Username FROM `ftp_accounts` INNER JOIN users ON ftp_accounts.User_id = users.User_id WHERE Is_Active=1 AND `ftp_accounts`.`Account_Id`=%s AND users.Admin_id=%s', (AccID, str(session['id'])))
            row = cursor.fetchone()
            if row is None:
                flash('FTP Account not found or access denied.')
                return redirect(url_for('routes.admin_viewAccounts'))
            ftpUsername = row[0]
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                # FIXED: fully parameterized — EncodedPassword no longer concatenated
                cursor.execute('UPDATE `ftp_accounts` SET `FTP_Password` = %s WHERE `ftp_accounts`.`Account_Id` = %s', (EncodedPassword, AccID))
                mysqlconnection.commit()
                if cursor.rowcount > 0:
                    change_ftp_pass(ftpUsername, pass1)
                    msg = {'error': 'success', 'message': 'FTP Account Password Updated.'}
                    return render_template('adminFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('adminFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('adminFiles/ftpAccounts/updateAccountPass.html', database=AccID, msg=msg)
        else:
            # FIX R13-04: was redirecting to admin_viewDatabases (wrong page for FTP accounts)
            return redirect(url_for("routes.admin_viewAccounts"))
    else:
        return redirect(url_for('routes.login'))



@routes.route('/admin/FTPAccounts/deleteAccount', methods =['GET', 'POST'])
def admin_deleteAccount():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')
            cursor = mysqlconnection.cursor()
            # FIX R11-04: IDOR — no Admin_id ownership check; any admin could delete any FTP account
            cursor.execute(
                'SELECT FTP_Username FROM `ftp_accounts` '
                'INNER JOIN users ON ftp_accounts.User_id = users.User_id '
                'WHERE ftp_accounts.Is_Active=1 AND ftp_accounts.Account_Id=%s AND users.Admin_id=%s',
                (AccID, str(session['id']))
            )
            row = cursor.fetchone()
            # FIX R7-02: null-pointer crash if AccID not found
            if row is None:
                flash('FTP Account not found or access denied.')
                return redirect(url_for('routes.admin_viewAccounts'))
            ftpUsername = row[0]
            # FIX R12-02/03: scope the UPDATE to this admin's own FTP accounts
            # The SELECT check above prevents IDOR on fetch, but the UPDATE itself
            # must also include the Admin_id scope to prevent race-condition bypass.
            cursor.execute(
                "UPDATE `ftp_accounts` "
                "SET `Is_Active` = '0' "
                "WHERE `ftp_accounts`.`Account_Id` =%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (AccID, str(session['id']))
            )
            mysqlconnection.commit()
            if cursor.rowcount>0:
                remove_ftp(ftpUsername)
                flash('FTP Account Deleted.')
                return redirect(url_for("routes.admin_viewAccounts"))
            else:
                flash('FTP Account Not Deleted.')
                return redirect(url_for("routes.admin_viewAccounts"))

        else:
            return redirect(url_for("routes.admin_viewAccounts"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/ftpServer')
def admin_ftpServer():
    mysqlconnection.reconnect()
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/ftpAccounts/ftpServer.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/addEmail', methods=['GET','POST'])
def admin_addEmail():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # Fetch users for the dropdown — domains load dynamically via AJAX
        cursor.execute(
            'SELECT User_id, User_Name, User_email FROM `users` '
            'WHERE Is_Deleted=0 AND Admin_id=%s ORDER BY User_Name;',
            (str(session['id']),)
        )
        users = cursor.fetchall()

        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form and 'Password' in request.form:
            domainID = request.form['domainID']
            if domainID == '':
                flash('Please select a domain.')
                return render_template('adminFiles/Mails/addEmail.html', users=users, msg='')
            suffix = request.form['suffix']
            # FIX NEW-03: validate suffix to prevent injection into mail address and downstream XSS
            try:
                suffix = sanitize_shell_arg(suffix, 'suffix')
            except ValueError:
                flash('Invalid email prefix. Use only letters, digits, and hyphens.')
                return render_template('adminFiles/Mails/addEmail.html', users=users, msg='')
            Password = request.form['Password']
            encodedPass = Base64Encode(Password)
            cursor.execute(
                "SELECT * FROM `domains` "
                "WHERE Is_Deleted=0 AND Domain_Id=%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (domainID, str(session['id']))
            )
            rDomain = cursor.fetchone()
            # FIX D-10: IDOR — domainID verified to belong to this admin's users
            if rDomain is None:
                flash('Domain not found or access denied.')
                return render_template('adminFiles/Mails/addEmail.html', users=users, msg='')
            mail_adress = suffix + '@' + rDomain[1]
            userID = str(rDomain[2])
            try:
                cursor.execute(
                    "INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) "
                    "VALUES (NULL,%s,%s,%s,%s,'1')",
                    (domainID, userID, mail_adress, encodedPass)
                )
                mysqlconnection.commit()
            except Exception:
                flash('Mail account already exists.')
                return render_template('adminFiles/Mails/addEmail.html', users=users, msg='')
            if cursor.rowcount > 0:
                create_mail_user(cursor, mail_adress, Password)
                flash('Email account created successfully.')
                return redirect(url_for('routes.admin_viewEmail'))
            else:
                flash('Mail account not added.')
                return render_template('adminFiles/Mails/addEmail.html', users=users, msg='')
        # GET — render blank form
        return render_template('adminFiles/Mails/addEmail.html', users=users, msg='')
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/EmailAccounts/viewEmail')
def admin_viewEmail():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R14-08: info-leak — was showing ALL mail accounts from all admins
        cursor.execute(
            'SELECT * FROM mail_accounts '
            'LEFT JOIN users ON users.User_id = mail_accounts.User_id '
            'LEFT JOIN domains ON domains.Domain_Id = mail_accounts.Domain_Id '
            'WHERE mail_accounts.Is_Active = 1 AND users.Admin_id=%s',
            (str(session['id']),)
        )
        results = cursor.fetchall()
        # Also fetch users list for the 'Add Mail Account' form dropdown
        cursor.execute(
            'SELECT User_id, User_Name, User_email FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;',
            (str(session['id']),)
        )
        users = cursor.fetchall()
        msg = ''
        return render_template('adminFiles/Mails/viewEmail.html', results=results, users=users)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/deleteEmail', methods =['GET', 'POST'])
def admin_deleteEmail():
    mysqlconnection.reconnect()
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('mailID'):
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            # FIX R6-04: add Admin_id ownership check to prevent cross-admin mail account deletion
            cursor.execute(
                "UPDATE `mail_accounts` SET `Is_Active` = '0' "
                "WHERE `mail_accounts`.`Mail_Id` =%s "
                "AND `User_id` IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (mailID, str(session['id']))
            )
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('Email Account Deleted.')
                return redirect(url_for("routes.admin_viewEmail"))
            else:
                flash('Email Account not Deleted.')
                return redirect(url_for("routes.admin_viewEmail"))

        else:
            return redirect(url_for("routes.admin_viewEmail"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/EmailAccounts/updateEmail', methods=['GET', 'POST'])
def admin_updateEmail():
    mysqlconnection.reconnect()
    if check_admin_Login():
        msg=''
        if request.method == 'GET' and request.args.get('mailID'):
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            # FIX R8-05: IDOR — scope GET to admin's own mail accounts only
            cursor.execute(
                "SELECT * FROM `mail_accounts` "
                "WHERE Mail_Id=%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (mailID, str(session['id']))
            )
            mail = cursor.fetchone()
            if mail is None:
                flash('Mail account not found or access denied.')
                return redirect(url_for('routes.admin_viewEmail'))
            return render_template('adminFiles/Mails/updateEmail.html', mail=mailID, email=mail[3])
        elif request.method == 'POST' and 'mailID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            mailID = request.form['mailID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                # FIX R8-06: IDOR — scope POST update to admin's own mail accounts
                cursor.execute(
                    "UPDATE `mail_accounts` SET `Mail_Pass` = %s "
                    "WHERE `mail_accounts`.`Mail_Id` = %s "
                    "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                    (EncodedPassword, mailID, str(session['id']))
                )

                mysqlconnection.commit()
                if cursor.rowcount>0:
                    # FIX R21-02: re-scope Mail_Address SELECT to this admin's accounts (TOCTOU)
                    cursor.execute(
                        "SELECT Mail_Address FROM `mail_accounts` "
                        "WHERE Mail_Id=%s AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                        (mailID, str(session['id']))
                    )
                    mail = cursor.fetchone()
                    change_mail_password(cursor,mail[0],pass1)
                    msg = {"error": "success", "message": "Mail Account Password Updated."}
                    return render_template('adminFiles/Mails/updateEmail.html', mail=mailID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('adminFiles/Mails/updateEmail.html', mail=mailID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('adminFiles/Mails/updateEmail.html', mail=mailID, msg=msg)
        else:
            return redirect(url_for("routes.admin_viewEmail"))
    else:
        return redirect(url_for('routes.login'))





@routes.route('/admin/SubDomains/addSubDomain', methods=['GET','POST'])
def admin_addSubDomain():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R13-01: info-leak — was showing ALL domains from all admins in dropdown
        cursor.execute(
            'SELECT * FROM `domains` WHERE Is_Deleted=0 '
            'AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s);',
            (str(session['id']),)
        )
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form :
            domainID = request.form['domainID']
            if(domainID==""):
                flash('Domain not selected.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            # FIX R10-01: IDOR — verify domainID belongs to this admin before adding subdomain
            cursor.execute(
                'SELECT servUser FROM `users` INNER JOIN domains ON users.User_id = domains.User_id '
                'WHERE domains.Is_Deleted=0 AND Domain_Id=%s AND users.Admin_id=%s',
                (domainID, str(session['id']))
            )
            row = cursor.fetchone()
            if row is None:
                flash('Domain not found or access denied.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            getUserName = row[0]
            suffix = request.form['suffix']
            # FIXED VULN-11: validate suffix to prevent XSS + vhost injection
            try:
                suffix = sanitize_shell_arg(suffix, 'suffix')
            except ValueError:
                flash('Invalid subdomain prefix. Use only letters, digits, and hyphens.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            cursor.execute("SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id=%s", (domainID,))
            rDomain = cursor.fetchone()
            # FIX R13-08: NullPointer — rDomain[1] crashes if domainID was tampered
            if rDomain is None:
                flash('Domain not found.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            SubDomainAdress = suffix + '.' + rDomain[1]
            userID= str(rDomain[2])
            try:
                cursor.execute("INSERT INTO `subdomains` (`SDomain_ID`, `Domain_Id`, `User_id`, `SubDomain`, `Is_Active`) VALUES (NULL,%s,%s,%s, '1')",(domainID,userID,SubDomainAdress))
                mysqlconnection.commit()
            except:
                flash('Subdomain already exists.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            if cursor.rowcount>0:
                add_vhost(getUserName, SubDomainAdress)
                flash('Subdomain created successfully.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            else:
                flash('Subdomain not added.')
                return redirect(url_for('routes.admin_viewSubDomains'))
        else:
            return redirect(url_for('routes.admin_viewSubDomains'))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/SubDomains/viewSubDomains')
def admin_viewSubDomains():
    mysqlconnection.reconnect()
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        # FIX R13-02: info-leak — was showing ALL subdomains from all admins
        cursor.execute(
            'SELECT * FROM subdomains '
            'LEFT JOIN users ON users.User_id = subdomains.User_id '
            'LEFT JOIN domains ON domains.Domain_Id = subdomains.Domain_Id '
            'WHERE subdomains.Is_Active = 1 AND users.Admin_id=%s',
            (str(session['id']),)
        )
        results = cursor.fetchall()
        # UI: also fetch domains for embedded Add Subdomain tab
        cursor.execute(
            'SELECT * FROM `domains` WHERE Is_Deleted=0 '
            'AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s);',
            (str(session['id']),)
        )
        domains = cursor.fetchall()
        return render_template('adminFiles/SubDomains/viewSubDomains.html', results=results, domains=domains)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/SubDomains/deleteSubdomain', methods =['GET', 'POST'])
def admin_deleteSubDomain():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('SdomainID'):
            SdomainID=request.args.get('SdomainID')
            cursor = mysqlconnection.cursor()
            cursor.execute(
                'SELECT SubDomain FROM `subdomains` '
                'WHERE Is_Active=1 AND `subdomains`.`SDomain_ID`=%s '
                'AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)',
                (SdomainID, str(session['id']))
            )
            row = cursor.fetchone()
            # FIX R8-02: NullPointer crash + IDOR — no Admin_id ownership check before
            if row is None:
                flash('Subdomain not found or access denied.')
                return redirect(url_for('routes.admin_viewSubDomains'))
            SubDomainName = row[0]
            # FIX R13-03: IDOR — UPDATE was not scoped to admin's own subdomains
            cursor.execute(
                "UPDATE `subdomains` SET `Is_Active` = '0' "
                "WHERE `subdomains`.`SDomain_ID` =%s "
                "AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (SdomainID, str(session['id']))
            )
            mysqlconnection.commit()
            if cursor.rowcount>0:
                remove_vhost(SubDomainName)
                flash('Subdomain Deleted.')
                return redirect(url_for("routes.admin_viewSubDomains"))
            else:
                flash('Subdomain Not Deleted.')
                return redirect(url_for("routes.admin_viewSubDomains"))

        else:
            return redirect(url_for("routes.admin_viewSubDomains"))
    else:
        return redirect(url_for('routes.login'))





@routes.route('/admin/Logs/error_Logs')
def admin_error_logs():
    # Error logs merged into access_logs tab page — redirect
    if check_admin_Login():
        return redirect(url_for('routes.admin_access_logs'))
    return redirect(url_for('routes.login'))

@routes.route('/admin/Logs/error_Logs/Ajax' , methods = ['GET', 'POST'])
def admin_error_logs_ajax():
    mysqlconnection.reconnect()
    if check_admin_Login():
        adminID = str(session['id'])
        domainID = request.args.get('domainID')
        Result = {'data': ''}
        cursor = mysqlconnection.cursor()
        # FIXED VULN-06: added Admin_id ownership check to prevent IDOR
        # FIXED VULN-02: domain resolved from DB, never from user input
        cursor.execute(
            'SELECT servUser, Domain_Name FROM `domains` '
            'INNER JOIN users ON domains.User_id = users.User_id '
            'WHERE domains.Is_Deleted=0 AND domains.Domain_Id=%s AND users.Admin_id=%s',
            (domainID, adminID)
        )
        domainData = cursor.fetchone()
        if domainData is None:
            return current_app.response_class(response=json.dumps({'data': 'Access denied.'}), status=403, mimetype='application/json')
        userName = domainData[0]
        Domain = domainData[1]
        # FIXED VULN-02: validate domain from DB before building path
        try:
            safe_domain = sanitize_log_filename(Domain)
            safe_user = sanitize_shell_arg(userName, 'username')
        except ValueError:
            return current_app.response_class(response=json.dumps({'data': 'Invalid log path.'}), status=400, mimetype='application/json')
        base_dir = f'/home/{safe_user}/logs'
        try:
            fname = safe_log_path(base_dir, safe_domain, '-error.log')
        except ValueError:
            return current_app.response_class(response=json.dumps({'data': 'Invalid log path.'}), status=400, mimetype='application/json')
        raw = readLines(fname, 100)
        # FIXED VULN-13: HTML-escape log content to prevent second-order XSS
        Result['data'] = sanitize_log_content(raw)
        response = current_app.response_class(
            response=json.dumps(Result),
            status=200,
            mimetype='application/json'
        )
        return response
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Logs/access_logs')
def admin_access_logs():
    mysqlconnection.reconnect()
    if check_admin_Login():
        msg = ''
        cursor = mysqlconnection.cursor()
        # FIX R13-06: info-leak — was showing ALL domains from all admins in log viewer dropdown
        cursor.execute(
            'SELECT * FROM `domains` WHERE Is_Deleted=0 '
            'AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s)',
            (str(session['id']),)
        )
        domains = cursor.fetchall()
        return render_template('adminFiles/Logs/access_logs.html', msg=msg, domains=domains)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Logs/access_Logs/Ajax' , methods = ['GET', 'POST'])
def admin_access_logs_ajax():
    mysqlconnection.reconnect()
    if check_admin_Login():
        adminID = str(session['id'])
        domainID = request.args.get('domainID')
        Result = {'data': ''}
        cursor = mysqlconnection.cursor()
        # FIXED VULN-06 + VULN-02: ownership check + safe path construction
        cursor.execute(
            'SELECT servUser, Domain_Name FROM `domains` '
            'INNER JOIN users ON domains.User_id = users.User_id '
            'WHERE domains.Is_Deleted=0 AND domains.Domain_Id=%s AND users.Admin_id=%s',
            (domainID, adminID)
        )
        domainData = cursor.fetchone()
        if domainData is None:
            return current_app.response_class(response=json.dumps({'data': 'Access denied.'}), status=403, mimetype='application/json')
        userName = domainData[0]
        Domain = domainData[1]
        try:
            safe_domain = sanitize_log_filename(Domain)
            safe_user = sanitize_shell_arg(userName, 'username')
        except ValueError:
            return current_app.response_class(response=json.dumps({'data': 'Invalid log path.'}), status=400, mimetype='application/json')
        base_dir = f'/home/{safe_user}/logs'
        try:
            fname = safe_log_path(base_dir, safe_domain, '-access.log')
        except ValueError:
            return current_app.response_class(response=json.dumps({'data': 'Invalid log path.'}), status=400, mimetype='application/json')
        raw = readLines(fname, 100)
        Result['data'] = sanitize_log_content(raw)
        response = current_app.response_class(
            response=json.dumps(Result),
            status=200,
            mimetype='application/json'
        )
        return response
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/CronJobs/cron_jobs' ,methods = ['GET', 'POST'])
def admin_cron_jobs():
    mysqlconnection.reconnect()
    if check_admin_Login():
        msg = ''
        cursor = mysqlconnection.cursor()
        # FIX R11-05: show only cron jobs belonging to this admin's users
        cursor.execute(
            'SELECT * FROM `cronjobs` INNER JOIN users ON users.User_id = cronjobs.User_id '
            'WHERE cronjobs.Is_Deleted=0 AND users.Admin_id=%s;',
            (str(session['id']),)
        )
        cronjobs = cursor.fetchall()
        # FIX R11-06: show only this admin's own users in dropdown
        cursor.execute('SELECT User_id,User_email FROM `users` WHERE Is_Deleted=0 AND Admin_id=%s;', (str(session['id']),))
        users = cursor.fetchall()
        if request.method == 'POST' and 'userID' in request.form and 'CronTime' in request.form and 'Command' in request.form and 'logFile' in request.form:
            userID = request.form['userID']
            # FIX R8-03: IDOR — admin could set cron for any user, not just their own
            # Verify userID belongs to a user under this admin
            cursor.execute('SELECT User_id FROM users WHERE User_id=%s AND Admin_id=%s AND Is_Deleted=0', (userID, str(session['id'])))
            if cursor.fetchone() is None:
                msg = {'error': 'danger', 'message': 'User not found or access denied.'}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            CronTime = request.form['CronTime']
            Command = request.form['Command']
            logFile = request.form['logFile']
            # FIXED VULN-01: sanitize cron command — block shell metacharacters
            try:
                Command = sanitize_cron_command(Command)
            except ValueError as e:
                msg = {'error': 'danger', 'message': str(e)}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            # FIXED VULN-10: sanitize logFile — prevent path traversal
            try:
                logFile = sanitize_shell_arg(logFile, 'logfile')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid log filename. Use only letters, digits, dots, underscores, hyphens.'}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s', (userID,))
            # FIX R21-01: null guard — fetchone()[0] crashes if user deleted between ownership check and here
            _serv = cursor.fetchone()
            if _serv is None:
                msg = {'error': 'danger', 'message': 'User not found.'}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            getUsername = _serv[0]
            base_logs = f'/home/{getUsername}/crobjobs/logs'
            try:
                logFileLink = safe_log_path(base_logs, logFile)
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid log file path.'}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            CommandFinal = Command + ' >> ' + logFileLink
            cursor.execute("UPDATE `cronjobs` SET `Is_Deleted` = '1' WHERE `cronjobs`.`User_id` = %s", (userID,))
            my_cron = CronTab(user=getUsername)
            my_cron.remove_all()
            job = my_cron.new(command=CommandFinal)
            if CronTime == "oneminute":
                job.minute.every(1)
            elif CronTime == "fiveminute":
                job.minute.every(5)
            elif CronTime == "everyday":
                job.day.every(1)
            elif CronTime == "everymonth":
                job.month.every(1)
            else:
                msg = {"error": "danger", "message": "Cron Job Error."}
                # FIX R11-07: was rendering userFiles template inside admin route
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            # job.minute.every(1)
            my_cron.write()
            #query = "INSERT INTO `cronjobs` (`Job_ID`, `User_id`, `Cron_Command`, `Logs_Directory`, `Is_Deleted`) VALUES (NULL, '"+userID+"', '"+Command+"', '"+logFile+"', '0')"
            #print(query)
            cursor.execute("INSERT INTO `cronjobs` (`Job_ID`, `User_id`, `Cron_Command`, `Logs_Directory`, `Is_Deleted`) VALUES (NULL, %s, %s, %s, '0')",(userID,Command,logFile))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                # FIX R14-12: cron refresh was showing ALL users' cron jobs, not just this admin's
                cursor.execute(
                    'SELECT * FROM `cronjobs` INNER JOIN users ON users.User_id = cronjobs.User_id '
                    'WHERE cronjobs.Is_Deleted=0 AND users.Admin_id=%s;',
                    (str(session['id']),)
                )
                cronjobs = cursor.fetchall()
                msg = {"error": "success", "message": "Cron Job Added."}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            else:
                msg = {"error": "danger", "message": "Cron Job Not Added."}
                return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
            #return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
        else:
            return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/CronJobs/deleteJob', methods =['GET', 'POST'])
def admin_deleteJob():
    mysqlconnection.reconnect()
    # FIXED VULN-05: was check_user_Login() — any user could delete admin cron jobs
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'GET' and request.args.get('JobID'):
            JobID=request.args.get('JobID')
            cursor.execute(
                'SELECT servUser FROM `users` '
                'INNER JOIN cronjobs ON users.User_id=cronjobs.User_id '
                'WHERE cronjobs.Is_Deleted=0 AND cronjobs.Job_ID=%s '
                'AND users.Admin_id=%s',
                (JobID, str(session['id']))
            )
            row = cursor.fetchone()
            # FIX R8-04: NullPointer crash + IDOR — no Admin_id ownership before
            if row is None:
                flash('Cron job not found or access denied.')
                return redirect(url_for('routes.admin_cron_jobs'))
            getUsername = row[0]
            # FIX R16-07: IDOR — UPDATE had no Admin_id scope; SELECT verified ownership
            # but the UPDATE itself only filtered on Job_ID, allowing race-condition bypass.
            cursor.execute(
                "UPDATE `cronjobs` SET `Is_Deleted` = '1' "
                "WHERE `cronjobs`.`Job_ID` =%s "
                "AND `User_id` IN (SELECT User_id FROM users WHERE Admin_id=%s)",
                (JobID, str(session['id']))
            )
            mysqlconnection.commit()
            if cursor.rowcount>0:
                my_cron = CronTab(user=getUsername)
                my_cron.remove_all()
                #deleteCronJob(getUsername)
                flash('CronJobs Deleted.')
                return redirect(url_for("routes.admin_cron_jobs"))
            else:
                flash('CronJobs not Deleted.')
                return redirect(url_for("routes.admin_cron_jobs"))
        else:
            return redirect(url_for("routes.admin_cron_jobs"))
    else:
        return redirect(url_for('routes.login'))
