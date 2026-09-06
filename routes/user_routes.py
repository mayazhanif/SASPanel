import json
from flask import render_template, session, request, redirect, url_for, flash
from . import routes
from app import *
import functions
from functions import hash_password
from Database.DbConfig import mysqlconnection
from routes.security import (
    require_user, log_security_event,
    sanitize_shell_arg, sanitize_cron_command,
    sanitize_log_filename, safe_log_path, sanitize_log_content,
)
import functions
from urllib.parse import urlparse
from flask import current_app as app
from datetime import datetime
from datetime import timedelta
from crontab import CronTab

@routes.route('/user/dashboard')
def user_dashboard():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg=""
        # FIX R9-08: Host header injection — use trusted SERVER_NAME, not request.base_url
        mainhost = os.environ.get('SERVER_NAME') or request.host
        return render_template('userFiles/dashboard.html', msg=msg, mainhost=mainhost)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT packages.*, users.User_Reg_Date FROM packages INNER JOIN users ON packages.Package_Id = users.Package_id WHERE users.Is_Deleted=0 and users.User_id=%s',(str(session["id"]),))
        getPackage=cursor.fetchone()
        cgiAccess="Disabled"
        if getPackage[6]==1:
            cgiAccess="Enabled"
        cursor.execute('SELECT * FROM domains where  Is_Deleted=0 and User_id=%s',(str(session["id"]),))
        cursor.fetchall()
        countDomains = str(cursor.rowcount)
        cursor.execute('SELECT * FROM ftp_accounts where Is_Active=1 and User_id=%s',(str(session["id"]),))
        cursor.fetchall()
        countFTP = str(cursor.rowcount)
        cursor.execute('SELECT * FROM mail_accounts where Is_Active=1 and User_id=%s',(str(session["id"]),))
        cursor.fetchall()
        countMails = str(cursor.rowcount)
        cursor.execute('SELECT * FROM msqldatabases where Is_Active=1 and User_id=%s',(str(session["id"]),))
        cursor.fetchall()
        countDB = str(cursor.rowcount)
        cursor.execute('SELECT * FROM msqldatabases where Is_Active=1 and User_id=%s',(str(session["id"]),))
        cursor.fetchall()
        countSubDomain = str(cursor.rowcount)
        profileData = {
            'RegDate':    str(getPackage[11]),
            'PackageName': str(getPackage[1]),
            'FTP':        f'{countFTP}/{getPackage[3]}',
            'Mails':      f'{countMails}/{getPackage[4]}',
            'Domains':    f'{countDomains}/{getPackage[5]}',
            'CGI':        cgiAccess,
            'Mysql':      f'{countDB}/{getPackage[7]}',
            'SubDomains': f'{countSubDomain}/{getPackage[8]}',
            'Storage':    str(getPackage[9]),
        }

        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            # FIX: cap length to prevent oversized input from crashing DB or causing DoS
            if not Name or len(Name) > 128:
                return render_template('userFiles/profile.html', profileData=profileData, msg={"error": "danger", "message": "Name must be between 1 and 128 characters."})
            cursor.execute('UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                session["Name"]=Name;
                return render_template('userFiles/profile.html', profileData=profileData, msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('userFiles/profile.html', profileData=profileData, msg={"error":"primary","message":"Name not Updated."})
        elif request.method == 'POST' and 'pass1' in request.form and 'pass2' in request.form:
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                cursor = mysqlconnection.cursor()
                # FIXED: bcrypt instead of MD5
                securePassword = hash_password(pass1)
                cursor.execute('UPDATE `users` SET `User_Password` = %s WHERE User_id = %s;', (securePassword, session['id']))
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    return render_template('userFiles/profile.html', profileData=profileData, passmsg={"error":"success","message":"Password Updated Successfully."})
                else:
                    return render_template('userFiles/profile.html', profileData=profileData, passmsg={"error":"primary","message":"Password not Updated."})
            else:
                return render_template('userFiles/profile.html', profileData=profileData,
                                       passmsg={"error": "danger", "message": "Password and Confirm Password Mismatch."})
        else:
            return render_template('userFiles/profile.html', profileData=profileData)
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/domains/addDomain', methods = ['GET', 'POST'])
def user_addDomain():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'DomainName' in request.form:
            userID = str(session["id"])
            DomainName = request.form['DomainName']
            # FIX R7-05: validate DomainName before passing to add_vhost/generate_SSL
            try:
                DomainName = sanitize_shell_arg(DomainName, 'domain')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid domain name. Use only letters, digits, dots, hyphens.'}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            #querylimit ="SELECT Limit_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute("SELECT Limit_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id=%s",(userID,))
            # FIX R15-02: null guard — limit fetchone() crashes if user record is missing
            limit_row = cursor.fetchone()
            if limit_row is None:
                msg = {"error": "danger", "message": "User account error. Please contact support."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            limit = limit_row[0]
            #cursor.rowcount>
            #queryinUSe ="SELECT * FROM `domains` where User_id="+userID
            cursor.execute("SELECT * FROM `domains` where User_id=%s",(userID,))
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "Domains Limit Reached."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            cursor.execute('SELECT servUser,User_email FROM `users` where Is_Deleted=0 and User_id=%s',(userID,))
            user = cursor.fetchone()
            getUserName = user[0]
            getEmail = user[1]
            #query = "INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, '" + DomainName + "', '"+userID+"', '0', '0');"
            try:
                cursor.execute("INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, %s, %s, '0', '0');",(DomainName,userID))
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Domain Already Added."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            if cursor.rowcount > 0:
                DomainID = str(cursor.lastrowid)
                add_vhost(getUserName,DomainName)
                generate_SSL(DomainName,getEmail)
                ExpiryDate = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
                privatekey="/etc/letsencrypt/live/"+DomainName+"/privkey.pem"
                fullchain="/etc/letsencrypt/live/"+DomainName+"/fullchain.pem"
                #query = "INSERT INTO `sslcertificates` (`Cert_ID`, `Domain_Id`, `User_id`, `Certificate`, `PrivateKey`, `ExpiryDate`, `Is_Active`) VALUES (NULL, '"+DomainID+"', '"+userID+"', '/etc/letsencrypt/live/"+DomainName+"/fullchain.pem', '/etc/letsencrypt/live/"+DomainName+"/privkey.pem', '"+ExpiryDate+"', '1');"
                cursor.execute("INSERT INTO `sslcertificates` (`Cert_ID`, `Domain_Id`, `User_id`, `Certificate`, `PrivateKey`, `ExpiryDate`, `Is_Active`) VALUES (NULL, %s, %s, %s, %s, %s, '1');",(DomainID,userID,fullchain,privatekey,ExpiryDate))
                mysqlconnection.commit()
                add_mail_domain(cursor,DomainName)
                msg = {"error": "success", "message": "Domain Added."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            else:
                msg = {"error": "danger", "message": "Domain Not Added."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
        else:
            msg = ''
            return render_template('userFiles/domains/addDomain.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/domains/renewSSL', methods = ['GET','POST'])
def user_renewSSL():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        renewALLSSL()
        flash('SSL Certificates Renewed.')
        return redirect(url_for("routes.user_viewDomains"))
        #cursor.execute('SELECT * FROM `domains` where domains.Is_Deleted=0 and domains.User_id='+str(session["id"]))
        #cursor.execute('SELECT * FROM domains JOIN users ON domains.User_id = users.User_id JOIN sslcertificates ON sslcertificates.Domain_Id = domains.Domain_Id and domains.User_id='+str(session["id"]))
        #results = cursor.fetchall()
        #return render_template('userFiles/domains/viewDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/domains/viewDomains')
def user_viewDomains():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        #cursor.execute('SELECT * FROM `domains` where domains.Is_Deleted=0 and domains.User_id='+str(session["id"]))
        cursor.execute('SELECT * FROM domains JOIN users ON domains.User_id = users.User_id JOIN sslcertificates ON sslcertificates.Domain_Id = domains.Domain_Id and domains.User_id=%s',(str(session["id"]),))
        results = cursor.fetchall()
        return render_template('userFiles/domains/viewDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/domains/deleteDomain', methods =['GET', 'POST'])
def user_deleteDomain():
    mysqlconnection.reconnect()
    if check_user_Login():
        if request.method == 'GET' and request.args.get('domainID'):
            userID = str(session["id"])
            domainID=request.args.get('domainID')
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT Domain_Name FROM `domains` WHERE Is_Deleted=0 AND Domain_Id=%s AND User_id=%s',
                           (domainID, userID))
            row = cursor.fetchone()
            if row is None:
                flash('Domain not found or access denied.')
                return redirect(url_for('routes.user_viewDomains'))
            DomainName = row[0]
            # FIXED: fully parameterized, correct ownership check
            cursor.execute('UPDATE `domains` SET `Is_Deleted` = %s WHERE `Domain_Id` = %s AND User_id = %s',
                           ('1', domainID, userID))
            mysqlconnection.commit()
            if cursor.rowcount > 0:
                remove_vhost(DomainName)
                flash('Domain Deleted.')
                return redirect(url_for('routes.user_viewDomains'))
            else:
                flash('Domain not Deleted.')
                return redirect(url_for('routes.user_viewDomains'))

        else:
            return redirect(url_for("routes.user_viewDomains"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Databases/addDB', methods =['GET', 'POST'])
def user_addDB():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'databaseName' in request.form:
            #querylimit ="SELECT Limit_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id=%",(userID,)
            cursor.execute("SELECT Limit_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id=%s",(userID,))
            limit=cursor.fetchone()
            limit= limit[0]
            # FIXED: parameterized query (was raw string concatenation)
            cursor.execute('SELECT COUNT(*) FROM `domains` WHERE User_id=%s', (userID,))
            in_use = cursor.fetchone()[0]
            if in_use >= limit:
                msg = {"error": "danger", "message": "Mysql Databases Limit Reached."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
            cursor.execute(
                'SELECT * FROM `mysqldbusers` INNER JOIN users ON mysqldbusers.User_id = users.User_id where Is_Deleted=0 and users.User_id=%s',(userID,))
            DBUserbyID = cursor.fetchone()
            databaseName = request.form['databaseName']
            #query = "INSERT INTO `msqldatabases` (`DB_ID`, `DbName`, `User_id`, `DbUser_ID`, `Is_Active`) VALUES (NULL, '" + databaseName + "', '" + userID + "', '" + str(DBUserbyID[0]) + "', '1');"
            try:
                cursor.execute("INSERT INTO `msqldatabases` (`DB_ID`, `DbName`, `User_id`, `DbUser_ID`, `Is_Active`) VALUES (NULL, %s, %s, %s, '1');",(databaseName,userID,str(DBUserbyID[0])))
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Database name already in use."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
            if cursor.rowcount > 0:
                create_database(cursor,databaseName,DBUserbyID[1])
                msg = {"error": "success", "message": "Database Added."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
            else:
                msg = {"error": "danger", "message": "Database Adding not Successfull."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
        else:
            msg = ''
            return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/Databases/viewDatabases')
def user_viewDatabases():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        userID = str(session["id"])
        cursor.execute('SELECT * FROM mysqldbusers LEFT JOIN msqldatabases ON msqldatabases.DbUser_ID = mysqldbusers.DbUser_ID LEFT JOIN users ON users.User_id = mysqldbusers.User_id WHERE msqldatabases.Is_Active = 1 and mysqldbusers.User_id=%s',(userID,))
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/MysqlDatabase/viewDatabases.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Databases/deleteDatabase', methods =['GET', 'POST'])
def user_deleteDatabase():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('DbID'):
            DbID=request.args.get('DbID')
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT DbName FROM `msqldatabases` where DB_ID=%s and msqldatabases.User_id=%s',(DbID,userID))
            row = cursor.fetchone()
            # FIX R7-06: null-pointer crash if DB doesn't belong to this user
            if row is None:
                flash('Database not found or access denied.')
                return redirect(url_for('routes.user_viewDatabases'))
            getDBName = row[0]
            #query="UPDATE `msqldatabases` SET `Is_Active` = '0' WHERE `msqldatabases`.`DB_ID` = "+DbID+" and msqldatabases.User_id="+userID
            cursor.execute("UPDATE `msqldatabases` SET `Is_Active` = '0' WHERE `msqldatabases`.`DB_ID` = %s and msqldatabases.User_id=%s",(DbID,userID))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                drop_database(cursor,getDBName)
                flash('Database Deleted.')
                return redirect(url_for("routes.user_viewDatabases"))
            else:
                flash('Database not Deleted.')
                return redirect(url_for("routes.user_viewDatabases"))

        else:
            return redirect(url_for("routes.user_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/Databases/updateDBPass', methods=['GET', 'POST'])
def user_updateDBPass():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg=''
        cursor = mysqlconnection.cursor()
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('DbID'):
            DbUser_ID=request.args.get('DbID')
            #query="SELECT * FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` ="+DbUser_ID+" and User_id="+userID
            cursor.execute("SELECT * FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` =%s and User_id=%s",(DbUser_ID,userID))
            database = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=database[0])
            else:
                # FIX R10-07: was redirecting to admin_viewDatabases (wrong route for a user)
                return redirect(url_for("routes.user_viewDatabases"))
        elif request.method == 'POST' and 'DbID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            DbUser_ID = request.form['DbID']
            cursor.execute("SELECT DbUsername FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` =%s and User_id=%s",(DbUser_ID,userID))
            row = cursor.fetchone()
            # FIX R12-04: NullPointer — fetchone()[0] crashes if DbUser_ID not owned by this user
            if row is None:
                msg = {"error": "danger", "message": "Database not found or access denied."}
                return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
            mysqlUsername = row[0]
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                #query = "UPDATE `mysqldbusers` SET `DbPassword` = '"+EncodedPassword+"' WHERE `mysqldbusers`.`DbUser_ID` = "+DbUser_ID+" and User_id="+userID
                cursor.execute("UPDATE `mysqldbusers` SET `DbPassword` = %s WHERE `mysqldbusers`.`DbUser_ID` = %s and User_id=%s",(EncodedPassword,DbUser_ID,userID))
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    changePassword(cursor, mysqlUsername, pass1)
                    msg = {"error": "success", "message": "Database Password Updated."}
                    return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
        else:
            return redirect(url_for("routes.user_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/FTPAccounts/addAccounts', methods=['GET', 'POST'])
def user_addAccounts():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'ftpUsername' in request.form and 'ftpPassword' in request.form:
            userID = str(session["id"])
            #querylimit ="SELECT Limit_FTP FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute("SELECT Limit_FTP FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id=%s",(userID,))
            limit=cursor.fetchone()
            limit= limit[0]
            #cursor.rowcount>
            #queryinUSe ="SELECT * FROM `ftp_accounts` where User_id=%s",(userID,)
            cursor.execute("SELECT * FROM `ftp_accounts` where User_id=%s",(userID,))
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "FTP Account Limit Reached."}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
            ftpUsername = request.form['ftpUsername']
            ftpPassword = request.form['ftpPassword']
            # FIX R6-05: validate ftpUsername — it becomes a Linux OS username
            # Unvalidated username could inject special chars into useradd
            try:
                ftpUsername = sanitize_shell_arg(ftpUsername, 'username')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid FTP username. Use only lowercase letters, digits, hyphens, underscores.'}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
            encodedPass = Base64Encode(ftpPassword)
            Directory = "/home/username/public_html"
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s',(userID,))
            getUserName = cursor.fetchone()[0]
            #query = "INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES (NULL, '" + userID + "', '" + Directory + "', '" + ftpUsername + "', '" + encodedPass + "', '1');"
            try:
                cursor.execute("INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES (NULL, %s, %s, %s, %s, '1');",(userID,Directory,ftpUsername,encodedPass))
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "FTP Username Already in Use."}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
            if cursor.rowcount > 0:
                add_ftp(ftpUsername,getUserName,ftpPassword)
                msg = {"error": "success", "message": "FTP Account Added."}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
            else:
                msg = {"error": "danger", "message": "FTP account not added."}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
        else:
            msg = ''
            return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/viewAccounts')
def user_viewAccounts():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute(
            'SELECT * FROM `ftp_accounts` INNER JOIN users ON ftp_accounts.User_id = users.User_id where ftp_accounts.Is_Active=1 and ftp_accounts.User_id=%s',(userID,))
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/ftpAccounts/viewAccounts.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/updateAccountPass', methods=['GET', 'POST'])
def user_updateAccountPass():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg=''
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')

            cursor = mysqlconnection.cursor()
            #query="SELECT * FROM `ftp_accounts` where Account_Id="+AccID+" and ftp_accounts.User_id = "+userID
            cursor.execute("SELECT * FROM `ftp_accounts` where Account_Id=%s and ftp_accounts.User_id = %s",(AccID,userID))
            account = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('userFiles/ftpAccounts/updateAccountPass.html', account=account[0])
            else:
                return redirect(url_for("routes.user_viewAccounts"))
        elif request.method == 'POST' and 'AccID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            AccID = request.form['AccID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                cursor.execute(
                    'SELECT FTP_Username FROM `ftp_accounts` where Is_Active=1 and `ftp_accounts`.`Account_Id`=%s and ftp_accounts.User_id = %s',(AccID,userID))
                row = cursor.fetchone()
                # FIX R6-06: null-pointer crash if AccID doesn't belong to this user
                if row is None:
                    msg = {'error': 'danger', 'message': 'FTP Account not found or access denied.'}
                    return render_template('userFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
                ftpUsername = row[0]
                #query = "UPDATE `ftp_accounts` SET `FTP_Password` = '"+EncodedPassword+"' WHERE `ftp_accounts`.`Account_Id` = "+AccID+" and ftp_accounts.User_id = "+userID
                #print(query)
                cursor.execute("UPDATE `ftp_accounts` SET `FTP_Password` = %s WHERE `ftp_accounts`.`Account_Id` = %s and ftp_accounts.User_id = %s",(EncodedPassword,AccID,userID))
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    change_ftp_pass(ftpUsername,pass1)
                    msg = {"error": "success", "message": "FTP Account Password Updated."}
                    return render_template('userFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('userFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('userFiles/ftpAccounts/updateAccountPass.html', database=AccID, msg=msg)
        else:
            # FIX R12-05: was redirecting to user_viewDatabases (wrong page for FTP accounts)
            return redirect(url_for("routes.user_viewAccounts"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/FTPAccounts/deleteAccount', methods =['GET', 'POST'])
def user_deleteAccount():
    mysqlconnection.reconnect()
    if check_user_Login():
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')
            userID = str(session["id"])
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT FTP_Username FROM `ftp_accounts` where Is_Active=1 and `ftp_accounts`.`Account_Id`=%s and ftp_accounts.User_id=%s',(AccID,userID))
            row = cursor.fetchone()
            # FIX R6-07: null-pointer crash + silent failure if account doesn't belong to user
            if row is None:
                flash('FTP Account not found or access denied.')
                return redirect(url_for('routes.user_viewAccounts'))
            ftpUsername = row[0]
            #query="UPDATE `ftp_accounts` SET `Is_Active` = '0' WHERE `ftp_accounts`.`Account_Id` = "+AccID+" and ftp_accounts.User_id="+userID
            cursor.execute("UPDATE `ftp_accounts` SET `Is_Active` = '0' WHERE `ftp_accounts`.`Account_Id` = %s and ftp_accounts.User_id=%s",(AccID,userID))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                remove_ftp(ftpUsername)
                flash('FTP Account Deleted.')
                return redirect(url_for("routes.user_viewAccounts"))
            else:
                flash('FTP Account not Deleted.')
                return redirect(url_for("routes.user_viewAccounts"))

        else:
            return redirect(url_for("routes.user_viewAccounts"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/ftpServer')
def user_ftpServer():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg = ''
        return render_template('userFiles/ftpAccounts/ftpServer.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/EmailAccounts/addEmail', methods=['GET','POST'])
def user_addEmail():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id=%s',(userID,))
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form and 'Password' in request.form:
            #querylimit ="SELECT Limit_Mails FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute("SELECT Limit_Mails FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id=%s",(userID,))
            limit=cursor.fetchone()
            limit= limit[0]
            #cursor.rowcount>
            #queryinUSe ="SELECT * FROM `mail_accounts` where User_id="+userID
            cursor.execute("SELECT * FROM `mail_accounts` where User_id=%s",(userID,))
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "Mail Accounts Limit Reached."}
                return render_template('userFiles/Mails/addEmail.html', msg=msg)
            domainID = request.form['domainID']
            if(domainID==""):
                msg={"error":"danger", "message": "Domain not Selected."}
                # FIX R10-08: was rendering adminFiles template (wrong context for user)
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
            suffix = request.form['suffix']
            # FIX NEW-01: validate suffix before building email address — prevents stored XSS and
            # injection into the mail DB via specially crafted local-part (e.g. suffix="admin'--")
            try:
                suffix = sanitize_shell_arg(suffix, 'suffix')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid email prefix. Use only letters, digits, and hyphens.'}
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
            Password = request.form['Password']
            encodedPass = Base64Encode(Password)
            #query = "SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id=" + domainID + " and User_id="+userID
            cursor.execute("SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id=%s and User_id=%s",(domainID,userID))
            rDomain = cursor.fetchone()
            if rDomain is None:
                msg = {'error': 'danger', 'message': 'Domain not found or access denied.'}
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
            mail_adress = suffix + "@" + rDomain[1]
            userID = str(rDomain[2])
            #query = "INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES (NULL, '" + domainID + "', '" + userID + "', '" + mail_adress + "', '" + encodedPass + "', '1')"
            try:
                cursor.execute("INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES (NULL, %s, %s, %s, %s, '1')",(domainID,userID,mail_adress,encodedPass))
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Mail Account Already Exists."}
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
            if cursor.rowcount > 0:
                create_mail_user(cursor,mail_adress,Password)
                msg = {"error": "success", "message": "Mail Account Added."}
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
            else:
                msg = {"error": "danger", "message": "Mail Account not added."}
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
        else:
            msg = ''
            return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/EmailAccounts/viewEmail')
def user_viewEmail():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM mail_accounts LEFT JOIN users ON users.User_id = mail_accounts.User_id LEFT JOIN domains ON domains.Domain_Id = mail_accounts.Domain_Id WHERE mail_accounts.Is_Active = 1 AND mail_accounts.User_id=%s',(userID,))
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/Mails/viewEmail.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/EmailAccounts/deleteEmail', methods =['GET', 'POST'])
def user_deleteEmail():
    mysqlconnection.reconnect()
    if check_user_Login():
        if request.method == 'GET' and request.args.get('mailID'):
            userID = str(session["id"])
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            #query="UPDATE `mail_accounts` SET `Is_Active` = '0' WHERE `mail_accounts`.`Mail_Id` = "+mailID+" and User_id="+userID
            cursor.execute("UPDATE `mail_accounts` SET `Is_Active` = '0' WHERE `mail_accounts`.`Mail_Id` = %s and User_id=%s",(mailID,userID))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('Email Account Deleted.')
                return redirect(url_for("routes.user_viewEmail"))
            else:
                flash('Email Account not Deleted.')
                return redirect(url_for("routes.user_viewEmail"))

        else:
            return redirect(url_for("routes.user_viewEmail"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/EmailAccounts/updateEmail', methods=['GET', 'POST'])
def user_updateEmail():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg=''
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('mailID'):
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            #query="SELECT * FROM `mail_accounts` where Mail_Id="+mailID+" and User_id="+userID
            cursor.execute("SELECT * FROM `mail_accounts` where Mail_Id=%s and User_id=%s",(mailID,userID))
            mail = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('userFiles/Mails/updateEmail.html', mail=mail[0])
            else:
                return redirect(url_for("routes.user_viewEmail"))
        elif request.method == 'POST' and 'mailID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            mailID = request.form['mailID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                #query = "UPDATE `mail_accounts` SET `Mail_Pass` = '"+EncodedPassword+"' WHERE `mail_accounts`.`Mail_Id` = "+mailID+" and User_id="+userID
                cursor.execute("UPDATE `mail_accounts` SET `Mail_Pass` = %s WHERE `mail_accounts`.`Mail_Id` = %s and User_id=%s",(EncodedPassword,mailID,userID))
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    #query = "SELECT Mail_Address FROM `mail_accounts` where Mail_Id=" + mailID + " and User_id=" + userID
                    cursor.execute("SELECT Mail_Address FROM `mail_accounts` where Mail_Id=%s and User_id=%s",(mailID,userID))
                    mail = cursor.fetchone()
                    change_mail_password(cursor,mail[0],pass1)
                    msg = {"error": "success", "message": "Mail Account Password Updated."}
                    return render_template('userFiles/Mails/updateEmail.html', mail=mailID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('userFiles/Mails/updateEmail.html', mail=mailID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('userFiles/Mails/updateEmail.html', mail=mailID, msg=msg)
        else:
            return redirect(url_for("routes.user_viewEmail"))
    else:
        return redirect(url_for('routes.login'))






@routes.route('/user/SubDomains/addSubDomain', methods=['GET','POST'])
def user_addSubDomain():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id=%s',(userID,))
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form:
            #querylimit ="SELECT Sub_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute("SELECT Sub_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id=%s",(userID,))
            limit=cursor.fetchone()
            limit= limit[0]
            # FIX R15-03: restore SELECT servUser with null guard (original accidentally removed SELECT)
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s', (userID,))
            _serv_row = cursor.fetchone()
            if _serv_row is None:
                msg = {'error': 'danger', 'message': 'User not found. Please log in again.'}
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            getUserName = _serv_row[0]

            # FIXED VULN-03: parameterized query (was raw string concat)
            cursor.execute('SELECT COUNT(*) FROM `subdomains` WHERE User_id=%s AND Is_Active=1', (userID,))
            in_use = cursor.fetchone()[0]
            if in_use >= limit:
                msg = {"error": "danger", "message": "Subdomains Limit Reached."}
                return render_template('userFiles/SubDomains/addSubDomain.html', msg=msg)
            domainID = request.form['domainID']
            if(domainID==""):
                msg={"error":"danger", "message": "Domain not Selected."}
                # FIX R11-08: was rendering adminFiles/Mails template (wrong context for user)
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            # FIX NEW-02: read suffix from form FIRST, then validate
            suffix = request.form['suffix']
            try:
                suffix = sanitize_shell_arg(suffix, 'suffix')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid subdomain prefix. Use only letters, digits, and hyphens.'}
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            cursor.execute("SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id=%s and User_id=%s", (domainID, userID))
            rDomain = cursor.fetchone()
            # FIX R11-09: NullPointer — no null check before rDomain[1] if domain doesn't belong to this user
            if rDomain is None:
                msg = {'error': 'danger', 'message': 'Domain not found or access denied.'}
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            SubDomainAdress = suffix + '.' + rDomain[1]
            userID = str(rDomain[2])
            #query = "INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES (NULL, '" + domainID + "', '" + userID + "', '" + mail_adress + "', '" + encodedPass + "', '1')"
            #query = "INSERT INTO `subdomains` (`SDomain_ID`, `Domain_Id`, `User_id`, `SubDomain`, `Is_Active`) VALUES (NULL, '"+domainID+"', '"+userID+"', '"+SubDomainAdress+"', '1')"
            #print(query)
            try:
                cursor.execute("INSERT INTO `subdomains` (`SDomain_ID`, `Domain_Id`, `User_id`, `SubDomain`, `Is_Active`) VALUES (NULL, %s, %s, %s, '1')",(domainID,userID,SubDomainAdress))
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "SubDomain Already Exists."}
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            if cursor.rowcount > 0:
                add_vhost(getUserName, SubDomainAdress)
                msg = {"error": "success", "message": "SubDomain Added."}
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            else:
                msg = {"error": "danger", "message": "SubDomain not added."}
                return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
        else:
            msg = ''
            return render_template('userFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/SubDomains/viewSubDomains')
def user_viewSubDomains():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM subdomains LEFT JOIN users ON users.User_id = subdomains.User_id LEFT JOIN domains ON domains.Domain_Id = subdomains.Domain_Id WHERE subdomains.Is_Active = 1 AND subdomains.User_id=%s',(userID,))
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/SubDomains/viewSubDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/SubDomains/deleteSubDomain', methods =['GET', 'POST'])
def user_deleteSubDomain():
    mysqlconnection.reconnect()
    if check_user_Login():
        if request.method == 'GET' and request.args.get('SdomainID'):
            userID = str(session["id"])
            SdomainID=request.args.get('SdomainID')
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT SubDomain FROM `subdomains` where Is_Active=1 and `subdomains`.`SDomain_ID`=%s and subdomains.User_id=%s', (SdomainID, userID))
            row = cursor.fetchone()
            # FIX R7-07: null-pointer crash if subdomain doesn't belong to this user
            if row is None:
                flash('Subdomain not found or access denied.')
                return redirect(url_for('routes.user_viewSubDomains'))
            SubDomainName = row[0]
            # FIXED VULN-04: fully parameterized (was partially concatenated)
            cursor.execute("UPDATE `subdomains` SET `Is_Active` = '0' WHERE `subdomains`.`SDomain_ID` = %s AND User_id=%s", (SdomainID, userID))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                remove_vhost(SubDomainName)
                flash('Subdomain Deleted.')
                return redirect(url_for("routes.user_viewSubDomains"))
            else:
                flash('Subdomain not Deleted.')
                return redirect(url_for("routes.user_viewSubDomains"))

        else:
            return redirect(url_for("routes.user_viewSubDomains"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/error_Logs')
def user_error_logs():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id=%s',(userID,))
        domains = cursor.fetchall()
        return render_template('userFiles/Logs/error_logs.html', domains=domains,msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/error_Logs/Ajax' , methods = ['GET', 'POST'])
def user_error_logs_ajax():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session['id'])
        domainName = request.args.get('domainName')
        Result = {'data': ''}
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s', (userID,))
        userName = cursor.fetchone()[0]
        # FIXED VULN-02: validate domainName to prevent path traversal / LFI
        try:
            safe_domain = sanitize_log_filename(domainName)
            safe_user = sanitize_shell_arg(userName, 'username')
        except ValueError:
            return app.response_class(response=json.dumps({'data': 'Invalid domain name.'}), status=400, mimetype='application/json')
        # Verify the domain actually belongs to this user (IDOR prevention)
        cursor.execute('SELECT Domain_Name FROM `domains` WHERE Domain_Name=%s AND User_id=%s AND Is_Deleted=0', (safe_domain, userID))
        if cursor.fetchone() is None:
            log_security_event('IDOR_LOG_ACCESS', f'domain={safe_domain!r} user={userID}')
            return app.response_class(response=json.dumps({'data': 'Access denied.'}), status=403, mimetype='application/json')
        base_dir = f'/home/{safe_user}/logs'
        try:
            fname = safe_log_path(base_dir, safe_domain, '-error.log')
        except ValueError:
            return app.response_class(response=json.dumps({'data': 'Invalid log path.'}), status=400, mimetype='application/json')
        raw = readLines(fname, 100)
        # FIXED VULN-13: HTML-escape to prevent second-order XSS
        Result['data'] = sanitize_log_content(raw)
        response = app.response_class(
            response=json.dumps(Result),
            status=200,
            mimetype='application/json'
        )
        return response
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Logs/access_logs')
def user_access_logs():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id=%s',(userID,))
        domains = cursor.fetchall()
        return render_template('userFiles/Logs/access_logs.html', domains=domains, msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/access_Logs/Ajax' , methods = ['GET', 'POST'])
def user_access_logs_ajax():
    mysqlconnection.reconnect()
    if check_user_Login():
        userID = str(session['id'])
        domainName = request.args.get('domainName')
        Result = {'data': ''}
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s', (userID,))
        userName = cursor.fetchone()[0]
        # FIXED VULN-02: validate domainName + ownership check
        try:
            safe_domain = sanitize_log_filename(domainName)
            safe_user = sanitize_shell_arg(userName, 'username')
        except ValueError:
            return app.response_class(response=json.dumps({'data': 'Invalid domain name.'}), status=400, mimetype='application/json')
        cursor.execute('SELECT Domain_Name FROM `domains` WHERE Domain_Name=%s AND User_id=%s AND Is_Deleted=0', (safe_domain, userID))
        if cursor.fetchone() is None:
            log_security_event('IDOR_LOG_ACCESS', f'domain={safe_domain!r} user={userID}')
            return app.response_class(response=json.dumps({'data': 'Access denied.'}), status=403, mimetype='application/json')
        base_dir = f'/home/{safe_user}/logs'
        try:
            fname = safe_log_path(base_dir, safe_domain, '-access.log')
        except ValueError:
            return app.response_class(response=json.dumps({'data': 'Invalid log path.'}), status=400, mimetype='application/json')
        raw = readLines(fname, 100)
        Result['data'] = sanitize_log_content(raw)
        response = app.response_class(
            response=json.dumps(Result),
            status=200,
            mimetype='application/json'
        )
        return response
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/CronJobs/cron_jobs' ,methods = ['GET', 'POST'])
def user_cron_jobs():
    mysqlconnection.reconnect()
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `cronjobs` INNER JOIN users ON users.User_id = cronjobs.User_id where cronjobs.Is_Deleted=0 and cronjobs.User_id=%s ORDER BY `cronjobs`.`Job_ID` ASC LIMIT 1;',(userID,))
        cronjobs = cursor.fetchall()
        if request.method == 'POST' and 'CronTime' in request.form and 'Command' in request.form and 'logFile' in request.form:
            CommandFinal= ""
            unixCommand =""
            CronTime = request.form['CronTime']
            Command = request.form['Command']
            logFile = request.form['logFile']
            # FIXED VULN-01: block shell metacharacters in cron command
            try:
                Command = sanitize_cron_command(Command)
            except ValueError as e:
                msg = {'error': 'danger', 'message': str(e)}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            # FIXED VULN-10: prevent path traversal via logFile parameter
            try:
                logFile = sanitize_shell_arg(logFile, 'logfile')
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid log filename. Use only letters, digits, dots, underscores, hyphens.'}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id=%s', (userID,))
            getUsername = cursor.fetchone()[0]
            base_logs = f'/home/{getUsername}/crobjobs/logs'
            try:
                logFileLink = safe_log_path(base_logs, logFile)
            except ValueError:
                msg = {'error': 'danger', 'message': 'Invalid log file path.'}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            CommandFinal = Command + ' >> ' + logFileLink
            cursor.execute("UPDATE `cronjobs` SET `Is_Deleted` = '1' WHERE `cronjobs`.`User_id` = %s", (userID,))
            my_cron = CronTab(user=getUsername)
            my_cron.remove_all()
            job = my_cron.new(command=CommandFinal)
            if CronTime=="oneminute":
                job.minute.every(1)
            elif CronTime=="fiveminute":
                job.minute.every(5)
            elif CronTime=="everyday":
                job.day.every(1)
            elif CronTime=="everymonth":
                job.month.every(1)
            else:
                msg={"error":"danger","message":"Cron Job Error."}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            #job.minute.every(1)
            my_cron.write()
            #query = "INSERT INTO `cronjobs` (`Job_ID`, `User_id`, `Cron_Command`, `Logs_Directory`, `Is_Deleted`) VALUES (NULL, '"+userID+"', '"+Command+"', '"+logFile+"', '0')"
            #print(query)
            cursor.execute("INSERT INTO `cronjobs` (`Job_ID`, `User_id`, `Cron_Command`, `Logs_Directory`, `Is_Deleted`) VALUES (NULL, %s, %s, %s, '0')",(userID,Command,logFile))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                cursor.execute('SELECT * FROM `cronjobs` INNER JOIN users ON users.User_id = cronjobs.User_id where cronjobs.Is_Deleted=0 and cronjobs.User_id=%s ORDER BY `cronjobs`.`Job_ID` ASC LIMIT 1;',(userID,))
                cronjobs = cursor.fetchall()
                msg = {"error": "success", "message": "Cron Job Added."}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            else:
                msg = {"error": "danger", "message": "Cron Job Not Added."}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            #return render_template('adminFiles/CronJobs/cron_jobs.html', msg=msg, users=users, cronjobs=cronjobs)
        else:
            return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/CronJobs/deleteJob', methods =['GET', 'POST'])
def user_deleteJob():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'GET' and request.args.get('JobID'):
            userID = str(session["id"])
            JobID=request.args.get('JobID')
            cursor.execute('SELECT servUser FROM `users` INNER JOIN cronjobs ON  users.User_id=cronjobs.User_id where cronjobs.Is_Deleted=0 and cronjobs.Job_ID=%s and cronjobs.User_id=%s',(JobID,userID))
            row = cursor.fetchone()
            # FIX R9-06: NullPointer crash if job already deleted or doesn't belong to user
            if row is None:
                flash('Cron job not found or access denied.')
                return redirect(url_for('routes.user_cron_jobs'))
            getUsername = row[0]
            #query="UPDATE `cronjobs` SET `Is_Deleted` = '1' WHERE `cronjobs`.`Job_ID` = "+JobID+" and User_id="+userID
            cursor.execute("UPDATE `cronjobs` SET `Is_Deleted` = '1' WHERE `cronjobs`.`Job_ID` = %s and User_id=%s",(JobID,userID))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                #deleteCronJob(getUsername)
                my_cron = CronTab(user=getUsername)
                my_cron.remove_all()
                flash('CronJobs Deleted.')
                return redirect(url_for("routes.user_cron_jobs"))
            else:
                flash('CronJobs Not Deleted.')
                return redirect(url_for("routes.user_cron_jobs"))

        else:
            return redirect(url_for("routes.user_cron_jobs"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/notifcations/viewNotifications')
def user_viewNotifications():
    mysqlconnection.reconnect()
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        #cursor.execute('SELECT * FROM `domains` where domains.Is_Deleted=0 and domains.User_id='+str(session["id"]))
        cursor.execute('SELECT * FROM `notifications` where Is_Active=1 and User_id=%s',(str(session["id"]),))
        results = cursor.fetchall()
        return render_template('userFiles/notifications/viewNotifications.html', results=results)
    else:
        return redirect(url_for('routes.login'))
