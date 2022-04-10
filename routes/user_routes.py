import json

from flask import render_template, session, request, redirect, url_for
from . import routes
from app import *
import functions
from Database.DbConfig import mysqlconnection
import functions
from urllib.parse import urlparse
from flask import current_app as app


@routes.route('/user/dashboard')
def user_dashboard():
    if check_user_Login():
        msg=""
        o = urlparse(request.base_url)
        mainhost = o.hostname
        #print(o.hostname)
        return render_template('userFiles/dashboard.html', msg=msg, mainhost=mainhost)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if check_user_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT packages.*, users.User_Reg_Date FROM packages INNER JOIN users ON packages.Package_Id = users.Package_id WHERE users.Is_Deleted=0 and users.User_id='+str(session["id"]))
        getPackage=cursor.fetchone()
        cgiAccess="Disabled"
        if getPackage[6]==1:
            cgiAccess="Enabled"
        cursor.execute('SELECT * FROM domains where  Is_Deleted=0 and User_id='+str(session["id"]))
        cursor.fetchall()
        countDomains = str(cursor.rowcount)
        cursor.execute('SELECT * FROM ftp_accounts where Is_Active=1 and User_id='+str(session["id"]))
        cursor.fetchall()
        countFTP = str(cursor.rowcount)
        cursor.execute('SELECT * FROM mail_accounts where Is_Active=1 and User_id='+str(session["id"]))
        cursor.fetchall()
        countMails = str(cursor.rowcount)
        cursor.execute('SELECT * FROM msqldatabases where Is_Active=1 and User_id='+str(session["id"]))
        cursor.fetchall()
        countDB = str(cursor.rowcount)
        cursor.execute('SELECT * FROM msqldatabases where Is_Active=1 and User_id='+str(session["id"]))
        cursor.fetchall()
        countSubDomain = str(cursor.rowcount)
        profileData = '{"RegDate" : "'+str(getPackage[11])+'", "PackageName" : "'+str(getPackage[1])+'", "FTP" : "'+countFTP+'/'+str(getPackage[3])+'", "Mails" : "'+countMails+'/'+str(getPackage[4])+'", "Domains" : "'+countDomains+'/'+str(getPackage[5])+'", "CGI" : "'+cgiAccess+'", "Mysql" : "'+countDB+'/'+str(getPackage[7])+'", "SubDomains" : "'+countSubDomain+'/'+str(getPackage[8])+'", "Storage" : "'+str(getPackage[9])+'"}'
        profileData = json.loads(profileData)

        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
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
            if pass1==pass2:
                cursor = mysqlconnection.cursor()
                md5Password = md5encode(pass1)
                #query = 'UPDATE `users` SET `User_Password` = %s WHERE User_id = %s;', (Name,session['id'])
                #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
                #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
                cursor.execute('UPDATE `users` SET `User_Password` = %s WHERE User_id = %s;', (md5Password,session['id']))
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
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id='+userID+';')
            getUserName = cursor.fetchone()[0]
            query = "INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, '" + DomainName + "', '"+userID+"', '0', '0');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg = {"error": "danger", "message": "Domain Already Added."}
                return render_template('userFiles/domains/addDomain.html', msg=msg)
            if cursor.rowcount > 0:
                add_vhost(getUserName,DomainName)
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
                create_database(cursor,databaseName,DBUserbyID[1])
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
            cursor.execute('SELECT DbName FROM `msqldatabases` where DB_ID='+DbID+' and msqldatabases.User_id='+userID+';')
            #print(cursor.fetchone()[0])
            getDBName = cursor.fetchone()[0]
            query="UPDATE `msqldatabases` SET `Is_Active` = '0' WHERE `msqldatabases`.`DB_ID` = "+DbID+" and msqldatabases.User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                drop_database(cursor,getDBName)
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
        cursor = mysqlconnection.cursor()
        userID = str(session["id"])
        if request.method == 'GET' and request.args.get('DbID'):
            DbUser_ID=request.args.get('DbID')
            query="SELECT * FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` ="+DbUser_ID+" and User_id="+userID
            cursor.execute(query)
            database = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('userFiles/MysqlDatabase/updateDBPass.html', database=database[0])
            else:
                return redirect(url_for("routes.admin_viewDatabases"))
        elif request.method == 'POST' and 'DbID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            DbUser_ID = request.form['DbID']
            query="SELECT DbUsername FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` ="+DbUser_ID+" and User_id="+userID
            cursor.execute(query)
            mysqlUsername = cursor.fetchone()[0]
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                query = "UPDATE `mysqldbusers` SET `DbPassword` = '"+EncodedPassword+"' WHERE `mysqldbusers`.`DbUser_ID` = "+DbUser_ID+" and User_id="+userID
                cursor.execute(query)
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
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id='+userID+';')
            getUserName = cursor.fetchone()[0]
            query = "INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES (NULL, '" + userID + "', '" + Directory + "', '" + ftpUsername + "', '" + encodedPass + "', '1');"
            try:
                cursor.execute(query)
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
                cursor.execute(
                    'SELECT FTP_Username FROM `ftp_accounts` where Is_Active=1 and `ftp_accounts`.`Account_Id`=' + AccID + 'and ftp_accounts.User_id = '+userID+';')
                ftpUsername = cursor.fetchone()[0]
                query = "UPDATE `ftp_accounts` SET `FTP_Password` = '"+EncodedPassword+"' WHERE `ftp_accounts`.`Account_Id` = "+AccID+" and ftp_accounts.User_id = "+userID
                print(query)
                cursor.execute(query)
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
            cursor.execute('SELECT FTP_Username FROM `ftp_accounts` where Is_Active=1 and `ftp_accounts`.`Account_Id`='+AccID+' and ftp_accounts.User_id='+userID+';')
            ftpUsername = cursor.fetchone()[0]
            query="UPDATE `ftp_accounts` SET `Is_Active` = '0' WHERE `ftp_accounts`.`Account_Id` = "+AccID+" and ftp_accounts.User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                remove_ftp(ftpUsername)
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






@routes.route('/user/SubDomains/addSubDomain', methods=['GET','POST'])
def user_addSubDomain():
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id='+userID)
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form:
            querylimit ="SELECT Sub_Domains FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute(querylimit)
            limit=cursor.fetchone()
            limit= limit[0]
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id='+userID+';')
            getUserName = cursor.fetchone()[0]
            #cursor.rowcount>
            queryinUSe ="SELECT * FROM `domains` where User_id="+userID
            cursor.execute(queryinUSe)
            cursor.fetchall()
            if cursor.rowcount>=limit:
                msg = {"error": "danger", "message": "Subdomains Limit Reached."}
                return render_template('userFiles/SubDomains/addSubDomain.html', msg=msg)
            domainID = request.form['domainID']
            suffix = request.form['suffix']
            query = "SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id=" + domainID + " and User_id="+userID
            cursor.execute(query)
            rDomain = cursor.fetchone()
            SubDomainAdress = suffix + "." + rDomain[1]
            userID = str(rDomain[2])
            #query = "INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES (NULL, '" + domainID + "', '" + userID + "', '" + mail_adress + "', '" + encodedPass + "', '1')"
            query = "INSERT INTO `subdomains` (`SDomain_ID`, `Domain_Id`, `User_id`, `SubDomain`, `Is_Active`) VALUES (NULL, '"+domainID+"', '"+userID+"', '"+SubDomainAdress+"', '1')"
            #print(query)
            try:
                cursor.execute(query)
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
    if check_user_Login():
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM subdomains LEFT JOIN users ON users.User_id = subdomains.User_id LEFT JOIN domains ON domains.Domain_Id = subdomains.Domain_Id WHERE subdomains.Is_Active = 1 AND subdomains.User_id='+userID)
        results = cursor.fetchall()
        msg = ''
        return render_template('userFiles/SubDomains/viewSubDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/SubDomains/deleteSubDomain', methods =['GET', 'POST'])
def user_deleteSubDomain():
    if check_user_Login():
        if request.method == 'GET' and request.args.get('SdomainID'):
            userID = str(session["id"])
            SdomainID=request.args.get('SdomainID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `subdomains` SET `Is_Active` = '0' WHERE `subdomains`.`SDomain_ID` = "+SdomainID+" and User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.user_viewSubDomains"))
            else:
                return redirect(url_for("routes.user_viewSubDomains"))

        else:
            return redirect(url_for("routes.user_viewSubDomains"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/error_Logs')
def user_error_logs():
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id='+userID)
        domains = cursor.fetchall()
        return render_template('userFiles/Logs/error_logs.html', domains=domains,msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/error_Logs/Ajax' , methods = ['GET', 'POST'])
def user_error_logs_ajax():
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        domainName = request.args.get('domainName')
        Result = {"data":""}
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id='+userID)
        userName = cursor.fetchone()[0]
        #fname = "C:\\Users\\mayaz\\Desktop\\testfile.txt"
        fname = "/home/"+userName+"/logs/"+domainName+"-error.log"
        data = readLines(fname,100)
        Result["data"]=data;
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
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0 and User_id='+userID)
        domains = cursor.fetchall()
        return render_template('userFiles/Logs/access_logs.html', domains=domains, msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/Logs/access_Logs/Ajax' , methods = ['GET', 'POST'])
def user_access_logs_ajax():
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        domainName = request.args.get('domainName')
        Result = {"data":""}
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id='+userID)
        userName = cursor.fetchone()[0]
        fname = "/home/"+userName+"/logs/"+domainName+"-access.log"
        data = readLines(fname,100)
        Result["data"]=data;
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
    if check_user_Login():
        msg = ''
        userID = str(session["id"])
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `cronjobs` INNER JOIN users ON users.User_id = cronjobs.User_id where cronjobs.Is_Deleted=0 and cronjobs.User_id='+userID+';')
        cronjobs = cursor.fetchall()
        if request.method == 'POST' and 'CronTime' in request.form and 'Command' in request.form and 'logFile' in request.form:
            CommandFinal= ""
            unixCommand =""
            CronTime = request.form['CronTime']
            if CronTime=="oneminute":
                unixCommand = "* * * * *"
            elif CronTime=="fiveminute":
                unixCommand = "*/5 * * * *"
            elif CronTime=="everyday":
                unixCommand = "0 0 * * *"
            elif CronTime=="everymonth":
                unixCommand = "0 0 1 * *"
            else:
                msg={"error":"danger","message":"Cron Job Error."}
                return render_template('userFiles/CronJobs/cron_jobs.html', msg=msg, cronjobs=cronjobs)
            Command = request.form['Command']
            logFile = request.form['logFile']
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted =0 and User_id='+userID)
            getUsername = cursor.fetchone()[0]
            logFileLink = "/home/"+getUsername+"/crobjobs/logs/"+logFile
            CommandFinal = unixCommand+" "+ Command+ " >> "+logFileLink
            addCronJob(getUsername, CommandFinal, logFileLink)
            query = "INSERT INTO `cronjobs` (`Job_ID`, `User_id`, `Cron_Command`, `Logs_Directory`, `Is_Deleted`) VALUES (NULL, '"+userID+"', '"+Command+"', '"+logFile+"', '0')"
            #print(query)
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                cursor.execute(
                    'SELECT * FROM `cronjobs` INNER JOIN users ON users.User_id = cronjobs.User_id where cronjobs.Is_Deleted=0;')
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
    if check_user_Login():
        if request.method == 'GET' and request.args.get('JobID'):
            userID = str(session["id"])
            JobID=request.args.get('JobID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `cronjobs` SET `Is_Deleted` = '1' WHERE `cronjobs`.`Job_ID` = "+JobID+" and User_id="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.user_cron_jobs"))
            else:
                return redirect(url_for("routes.user_cron_jobs"))

        else:
            return redirect(url_for("routes.user_cron_jobs"))
    else:
        return redirect(url_for('routes.login'))