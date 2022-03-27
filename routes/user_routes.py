from flask import render_template, session, request, redirect, url_for
from . import routes
from app import *
import functions
from Database.DbConfig import mysqlconnection
import functions

@routes.route('/user/dashboard')
def user_dashboard():
    if check_user_Login():
        msg=""
        return render_template('userFiles/dashboard.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if check_user_Login():
        cursor = mysqlconnection.cursor()

        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
            cursor.execute('UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                session["Name"]=Name;
                return render_template('userFiles/profile.html', msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('userFiles/profile.html', msg={"error":"primary","message":"Name not Updated."})
        elif request.method == 'POST' and 'pass1' in request.form and 'pass2' in request.form:
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1==pass2:
                cursor = mysqlconnection.cursor()
                md5Password = md5encode(pass1)
                #query = 'UPDATE `users` SET `User_Password` = %s WHERE User_id = %s;', (Name,session['id'])
                #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
                #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
                cursor.execute('UPDATE `users` SET `User_Password` = %s WHERE User_id = %s;', (md5Password,session['id']))
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    return render_template('userFiles/profile.html', passmsg={"error":"success","message":"Password Updated Successfully."})
                else:
                    return render_template('userFiles/profile.html', passmsg={"error":"primary","message":"Password not Updated."})
            else:
                return render_template('userFiles/profile.html',
                                       passmsg={"error": "danger", "message": "Password and Confirm Password Mismatch."})
        else:
            return render_template('userFiles/profile.html') 
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/domains/addDomain', methods = ['GET', 'POST'])
def user_addDomain():
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'DomainName' in request.form:
            userID = str(session["id"])
            DomainName = request.form['DomainName']
            querylimit ="SELECT Limit_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute(querylimit)
            limit=cursor.fetchone()
            limit= limit[0]
            #cursor.rowcount>
            queryinUSe ="SELECT * FROM `domains` where User_id="+userID
            cursor.execute(queryinUSe)
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "Domains Limit Reached."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            query = "INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, '" + DomainName + "', '1', '0', '0');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Domain Already Added."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            if cursor.rowcount > 0:
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



@routes.route('/user/domains/viewDomains')
def user_viewDomains():
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where domains.Is_Deleted=0 and domains.User_id='+str(session["id"]))
        results = cursor.fetchall()
        return render_template('userFiles/domains/viewDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Packages/deleteDomain', methods =['GET', 'POST'])
def user_deleteDomain():
    if check_user_Login():
        if request.method == 'GET' and request.args.get('domainID'):
            domainID=request.args.get('domainID')
            cursor = mysqlconnection.cursor()
            #query='UPDATE `domains` SET `Is_Deleted` = '1' WHERE `domains`.`Domain_Id` ='+domainID+'domains.User_id='+str(session["id"])
            query="UPDATE `domains` SET `Is_Deleted` = '1' WHERE `domains`.`Domain_Id` ="+domainID+" and domains.User_id="+str(session["id"])
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.user_viewDomains"))
            else:
                return redirect(url_for("routes.user_viewDomains"))

        else:
            return redirect(url_for("routes.user_viewDomains"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Databases/addDB', methods =['GET', 'POST'])
def user_addDB():
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'databaseName' in request.form:
            querylimit ="SELECT Limit_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute(querylimit)
            limit=cursor.fetchone()
            limit= limit[0]
            #cursor.rowcount>
            queryinUSe ="SELECT * FROM `domains` where User_id="+userID
            cursor.execute(queryinUSe)
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "Mysql Databases Limit Reached."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
            cursor.execute(
                'SELECT * FROM `mysqldbusers` INNER JOIN users ON mysqldbusers.User_id = users.User_id where Is_Deleted=0 and users.User_id=' + userID + ';')
            DBUserbyID = cursor.fetchone()
            databaseName = request.form['databaseName']
            query = "INSERT INTO `msqldatabases` (`DB_ID`, `DbName`, `User_id`, `DbUser_ID`, `Is_Active`) VALUES (NULL, '" + databaseName + "', '" + userID + "', '" + str(
                DBUserbyID[0]) + "', '1');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Database name already in use."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
            if cursor.rowcount > 0:
                msg = {"error": "success", "message": "Database Added.."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
            else:
                msg = {"error": "danger", "message": "Database Adding not Successfull."}
                return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
        else:
            msg = ''
            return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/Databases/MysqlDatabase/viewDatabases')
def user_viewDatabases():
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        userID = str(session["id"])
        cursor.execute(
            'SELECT * FROM mysqldbusers LEFT JOIN msqldatabases ON msqldatabases.DbUser_ID = mysqldbusers.DbUser_ID LEFT JOIN users ON users.User_id = mysqldbusers.User_id WHERE msqldatabases.Is_Active = 1 and mysqldbusers.User_id='+userID)
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/MysqlDatabase/viewDatabases.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Databases/deleteDatabase', methods =['GET', 'POST'])
def user_deleteDatabase():
    if check_user_Login():
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('DbID'):
            DbID=request.args.get('DbID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `msqldatabases` SET `Is_Active` = '0' WHERE `msqldatabases`.`DB_ID` = "+DbID+" and mysqldbusers.User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.user_viewDatabases"))
            else:
                return redirect(url_for("routes.user_viewDatabases"))

        else:
            return redirect(url_for("routes.user_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/Databases/updateDBPass', methods=['GET', 'POST'])
def user_updateDBPass():
    if check_user_Login():
        msg=''
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('DbID'):
            DbUser_ID=request.args.get('DbID')
            cursor = mysqlconnection.cursor()
            query="SELECT * FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` ="+DbUser_ID+" and User_id="+userID
            cursor.execute(query)
            database = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=database[0])
            else:
                return redirect(url_for("routes.admin_viewDatabases"))
        elif request.method == 'POST' and 'DbID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            DbUser_ID = request.form['DbID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                query = "UPDATE `mysqldbusers` SET `DbPassword` = '"+EncodedPassword+"' WHERE `mysqldbusers`.`DbUser_ID` = "+DbUser_ID+" and User_id="+userID
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    msg = {"error": "success", "message": "Database Password Updated."}
                    return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
        else:
            return redirect(url_for("routes.admin_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/FTPAccounts/addAccounts', methods=['GET', 'POST'])
def user_addAccounts():
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        if request.method == 'POST' and 'ftpUsername' in request.form and 'ftpPassword' in request.form:
            userID = str(session["id"])
            querylimit ="SELECT Limit_FTP FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute(querylimit)
            limit=cursor.fetchone()
            limit= limit[0]
            #cursor.rowcount>
            queryinUSe ="SELECT * FROM `ftp_accounts` where User_id="+userID
            cursor.execute(queryinUSe)
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "FTP Account Limit Reached."}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
            ftpUsername = request.form['ftpUsername']
            ftpPassword = request.form['ftpPassword']
            encodedPass = Base64Encode(ftpPassword)
            Directory = "/home/username/public_html"
            query = "INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES (NULL, '" + userID + "', '" + Directory + "', '" + ftpUsername + "', '" + encodedPass + "', '1');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "FTP Username Already in Use."}
                return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
            if cursor.rowcount > 0:
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
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute(
            'SELECT * FROM `ftp_accounts` INNER JOIN users ON ftp_accounts.User_id = users.User_id where ftp_accounts.Is_Active=1 and ftp_accounts.User_id='+userID)
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/ftpAccounts/viewAccounts.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/updateAccountPass', methods=['GET', 'POST'])
def user_updateAccountPass():
    if check_user_Login\
                ():
        msg=''
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')

            cursor = mysqlconnection.cursor()
            query="SELECT * FROM `ftp_accounts` where Account_Id="+AccID+" and ftp_accounts.User_id = "+userID
            cursor.execute(query)
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
                query = "UPDATE `ftp_accounts` SET `FTP_Password` = '"+EncodedPassword+"' WHERE `ftp_accounts`.`Account_Id` = "+AccID+" and ftp_accounts.User_id = "+userID
                print(query)
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    msg = {"error": "success", "message": "FTP Account Password Updated."}
                    return render_template('userFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('userFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('userFiles/ftpAccounts/updateAccountPass.html', database=AccID, msg=msg)
        else:
            return redirect(url_for("routes.user_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/FTPAccounts/deleteAccount', methods =['GET', 'POST'])
def user_deleteAccount():
    if check_user_Login():
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')
            userID = str(session["id"])
            cursor = mysqlconnection.cursor()
            query="UPDATE `ftp_accounts` SET `Is_Active` = '0' WHERE `ftp_accounts`.`Account_Id` = "+AccID+" and ftp_accounts.User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.user_viewAccounts"))
            else:
                return redirect(url_for("routes.user_viewAccounts"))

        else:
            return redirect(url_for("routes.user_viewAccounts"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/ftpServer')
def user_ftpServer():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/ftpAccounts/ftpServer.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/EmailAccounts/addEmail', methods=['GET','POST'])
def user_addEmail():
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id='+userID)
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form and 'Password' in request.form:
            querylimit ="SELECT Limit_Mails FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute(querylimit)
            limit=cursor.fetchone()
            limit= limit[0]
            #cursor.rowcount>
            queryinUSe ="SELECT * FROM `mail_accounts` where User_id="+userID
            cursor.execute(queryinUSe)
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "Mail Accounts Limit Reached."}
                return render_template('userFiles/Mails/addEmail.html', msg=msg)
            domainID = request.form['domainID']
            suffix = request.form['suffix']
            Password = request.form['Password']
            encodedPass = Base64Encode(Password)
            query = "SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id=" + domainID + " and User_id="+userID
            cursor.execute(query)
            rDomain = cursor.fetchone()
            mail_adress = suffix + "@" + rDomain[1]
            userID = str(rDomain[2])
            query = "INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES (NULL, '" + domainID + "', '" + userID + "', '" + mail_adress + "', '" + encodedPass + "', '1')"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Mail Account Already Exists."}
                return render_template('userFiles/Mails/addEmail.html', domains=domains, msg=msg)
            if cursor.rowcount > 0:
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
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM mail_accounts LEFT JOIN users ON users.User_id = mail_accounts.User_id LEFT JOIN domains ON domains.Domain_Id = mail_accounts.Domain_Id WHERE mail_accounts.Is_Active = 1 AND mail_accounts.User_id='+userID)
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/Mails/viewEmail.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/EmailAccounts/deleteEmail', methods =['GET', 'POST'])
def user_deleteEmail():
    if check_user_Login():
        if request.method == 'GET' and request.args.get('mailID'):
            userID = str(session["id"])
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `mail_accounts` SET `Is_Active` = '0' WHERE `mail_accounts`.`Mail_Id` = "+mailID+" and User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.user_viewEmail"))
            else:
                return redirect(url_for("routes.user_viewEmail"))

        else:
            return redirect(url_for("routes.user_viewEmail"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/EmailAccounts/updateEmail', methods=['GET', 'POST'])
def user_updateEmail():
    if check_user_Login():
        msg=''
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('mailID'):
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            query="SELECT * FROM `mail_accounts` where Mail_Id="+mailID+" and User_id="+userID
            cursor.execute(query)
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
                query = "UPDATE `mail_accounts` SET `Mail_Pass` = '"+EncodedPassword+"' WHERE `mail_accounts`.`Mail_Id` = "+mailID+" and User_id="+userID
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount>0:
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

@routes.route('/user/Logs/error_Logs')
def user_error_logs():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/Logs/error_logs.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/access_logs')
def user_access_logs():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/Logs/access_logs.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

