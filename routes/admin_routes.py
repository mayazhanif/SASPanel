import base64

from flask import render_template, request,redirect, url_for, flash
from Database.DbConfig import mysqlconnection
import hashlib

from . import routes
from functions import *


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
        cursor = mysqlconnection.cursor()
        #cursor.execute('SELECT * FROM `users` where Is_Deleted=0;')
        cursor.execute('SELECT * FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0;')
        results = cursor.fetchall()
        return render_template('adminFiles/users/viewUser.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Packages/deleteUser', methods =['GET', 'POST'])
def admin_deleteUser():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('userID'):
            userID=request.args.get('userID')
            cursor = mysqlconnection.cursor()
            #query="UPDATE `packages` SET `Is_Active` = '0' WHERE `packages`.`Package_Id` ="+userID
            query="UPDATE `users` SET `Is_Deleted` = '1' WHERE `users`.`User_id` ="+userID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewUser"))
            else:
                return redirect(url_for("routes.admin_viewUser"))

        else:
            return redirect(url_for("routes.admin_viewUser"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('select * from users where Is_Deleted=0 and Admin_id='+str(session["id"]))
        cursor.fetchall()
        totalUsers=str(cursor.rowcount)
        cursor.execute('select Reg_Date from administrator where Admin_id='+str(session["id"]))
        details=cursor.fetchone()
        regDate=str(details[0])
        cursor.execute('SELECT * FROM `packages` where Is_Active=1 and Admin_id='+str(session["id"]))
        cursor.fetchall()
        totalPackages=str(cursor.rowcount)

        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
            cursor.execute('UPDATE `administrator` SET `Admin_Name` = %s WHERE Admin_id = %s;', (Name,session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                session["Name"]=Name;
                return render_template('adminFiles/profile.html',users=totalUsers,regDate=regDate,totalPackages=totalPackages, msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('adminFiles/profile.html',users=totalUsers,regDate=regDate,totalPackages=totalPackages, msg={"error":"primary","message":"Name not Updated."})
        elif request.method == 'POST' and 'pass1' in request.form and 'pass2' in request.form:
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1==pass2:
                cursor = mysqlconnection.cursor()
                md5Password = md5encode(pass1)
                #query = 'UPDATE `users` SET `User_Password` = %s WHERE User_id = %s;', (Name,session['id'])
                #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
                #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
                cursor.execute('UPDATE `administrator` SET `Admin_Password` = %s WHERE Admin_id = %s;', (md5Password,session['id']))
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    return render_template('adminFiles/profile.html',users=totalUsers,regDate=regDate,totalPackages=totalPackages, passmsg={"error":"success","message":"Password Updated Successfully."})
                else:
                    return render_template('adminFiles/profile.html',users=totalUsers,regDate=regDate,totalPackages=totalPackages, passmsg={"error":"primary","message":"Password not Updated."})
            else:
                return render_template('adminFiles/profile.html',users=totalUsers,regDate=regDate,totalPackages=totalPackages,
                                       passmsg={"error": "danger", "message": "Password and Confirm Password Mismatch."})
        else:
            return render_template('adminFiles/profile.html',users=totalUsers,regDate=regDate,totalPackages=totalPackages)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/users/adduser', methods=['GET', 'POST'])
def admin_addUser():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `packages` where Is_Active=1;')
        results = cursor.fetchall()
        if request.method == 'POST' and 'Name' in request.form and 'Email' in request.form and 'pass1' in request.form and 'pass2' in request.form and 'packageID' in request.form:
            User_Name = request.form['Name']
            Admin_id = str(session['id'])
            User_email = request.form['Email']
            User_Password = request.form['pass1']
            Confirm_Password = request.form['pass2']
            if User_Password== Confirm_Password:
                md5Password = hashlib.md5(User_Password.encode()).hexdigest()
                packageID = request.form['packageID']
                servUser = generateservUser(User_Name,User_email)
                cursor = mysqlconnection.cursor()
                # query = "INSERT INTO `packages` (`Package_Id`, `Package_Name`, `Admin_id`, `Limit_FTP`, `Limit_Mails`, `Limit_Domains`, `CGI_ACCESS`, `Limit_DB`, `Sub_Domains`, `Storage_Limit`) VALUES (NULL, '"+Package_Name+"', '"+Admin_id+"', '"+Limit_FTP+"', '"+Limit_Mails+"', '"+Limit_Domains+"', '"+CGI_ACCESS+"', '"+Limit_DB+"', '"+Sub_Domains+"', '"+Storage_Limit+"');"
                query = "INSERT INTO `users` (`User_id`, `servUser`, `User_email`, `User_Password`, `User_Name`, `UserResetToken`, `Token_Expiry`, `Admin_id`, `Package_id`, `Is_Deleted`, `User_Reg_Date`) VALUES (NULL, '"+servUser+"', '" + User_email + "', '" + md5Password + "', '" + User_Name + "', '', CURRENT_TIMESTAMP, '" + Admin_id + "', '" + packageID + "', '0', CURRENT_TIMESTAMP);"
                cursor.execute(query)
                add_default_user(servUser,User_Password)
                userID = str(cursor.lastrowid)
                mysqlconnection.commit()
                if cursor.rowcount > 0:
                    dbUser = generateservUser(User_Name, User_email)
                    dbPassword = generatePassword()
                    base64dbPassword = Base64Encode(dbPassword)
                    query = "INSERT INTO `mysqldbusers` (`DbUser_ID`, `DbUsername`, `DbPassword`, `User_id`, `Is_Active`) VALUES (NULL, '"+dbUser+"', '"+base64dbPassword+"', '"+userID+"', '1')"
                    cursor.execute(query)
                    mysqlconnection.commit()
                    createUser(cursor,dbUser,dbPassword)

                    # session["Name"]=Package_Name;
                    return render_template('adminFiles/users/addUser.html',
                                           msg={"error": "success", "message": "User Added Successfully."})
                else:
                    return render_template('adminFiles/users/addUser.html',
                                           msg={"error": "primary", "message": "Fill all fields Correctly."})
            else:
                return render_template('adminFiles/users/addUser.html',
                                       msg={"error": "primary", "message": "Password and Confirm Password does not Match."})
        else:
            return render_template('adminFiles/users/addUser.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/users/updateUser', methods =['GET', 'POST'])
def admin_updateUser():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('userID'):
            userID=request.args.get('userID')
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT * FROM `packages` where Is_Active=1;')
            results = cursor.fetchall()
            query="SELECT * FROM `users` INNER JOIN packages ON users.Package_id = packages.Package_Id where Is_Deleted=0 and User_id="+userID
            cursor.execute(query)
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
            md5Password = hashlib.md5(password.encode()).hexdigest()

            #Package_Name = request.form['packagename']
            cursor = mysqlconnection.cursor()
            query = "UPDATE `users` SET `Package_Id` = '"+packageID+"', `User_email` = '"+Email+"',`User_Password` = '"+md5Password+"', `User_Name` = '"+Name+"' WHERE `users`.`User_id` = "+userID+""
            print(query)
            #query = "UPDATE `packages` SET  `Name` = '"+Package_Name+"', `Limit_FTP` = '"+Limit_FTP+"', `Limit_Mails` = '"+Limit_Mails+"', `Limit_Domains` = '"+Limit_Domains+"', `CGI_ACCESS` = '"+CGI_ACCESS+"', `Limit_DB` = '"+Limit_DB+"', `Sub_Domains` = '"+Sub_Domains+"', `Storage_Limit` = '"+Storage_Limit+"' WHERE `packages`.`Package_Id` = "+packageID+""
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                flash('Please choose a different Shortcode, that one is already in use')
                return redirect(request.referrer)
            else:
                return redirect(request.referrer)
        else:
            return redirect(request.referrer)

    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Packages/addPackage' , methods=['GET', 'POST'])
def admin_addPackage():
    if check_admin_Login():
        if request.method == 'POST' and 'packagename' in request.form and 'domains' in request.form and 'dbs' in request.form and 'subdomains' in request.form and 'ftps' in request.form and 'mails' in request.form and 'storage' in request.form:
            Package_Name = request.form['packagename']
            Admin_id = str(session['id'])
            Limit_Domains = request.form['domains']
            Limit_DB = request.form['dbs']
            Limit_FTP = request.form['ftps']
            Limit_Mails = request.form['mails']
            Sub_Domains = request.form['subdomains']
            Storage_Limit = request.form['storage']
            #CGI_ACCESS = request.form.getlist('cgiAccess')
            #print(CGI_ACCESS)
            CGI_ACCESS='0'
            if request.form.get("cgiAccess"):
                CGI_ACCESS = '1'
            #print(CGI_ACCESS)
            cursor = mysqlconnection.cursor()
            query = "INSERT INTO `packages` (`Package_Id`, `Package_Name`, `Admin_id`, `Limit_FTP`, `Limit_Mails`, `Limit_Domains`, `CGI_ACCESS`, `Limit_DB`, `Sub_Domains`, `Storage_Limit`) VALUES (NULL, '"+Package_Name+"', '"+Admin_id+"', '"+Limit_FTP+"', '"+Limit_Mails+"', '"+Limit_Domains+"', '"+CGI_ACCESS+"', '"+Limit_DB+"', '"+Sub_Domains+"', '"+Storage_Limit+"');"
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                #session["Name"]=Package_Name;
                return render_template('adminFiles/Packages/addPackage.html', msg={"error":"success","message":"Package Added."})
            else:
                return render_template('adminFiles/Packages/addPackage.html', msg={"error":"primary","message":"Fill all fields Correctly."})

        else:
            return render_template('adminFiles/Packages/addPackage.html', title='Add package')
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Packages/viewPackages')
def admin_viewPackages():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `packages` where Is_Active=1;')
        results = cursor.fetchall()
        #msg=''
        return render_template('adminFiles/Packages/viewPackages.html', results=results)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Packages/updatePackage', methods =['GET', 'POST'])
def admin_updatePackage():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('packageID'):
            packageID=request.args.get('packageID')
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT * FROM `packages` where Package_Id='+packageID)
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
            Limit_Domains = request.form['domains']
            Limit_DB = request.form['dbs']
            Limit_FTP = request.form['ftps']
            Limit_Mails = request.form['mails']
            Sub_Domains = request.form['subdomains']
            Storage_Limit = request.form['storage']
            CGI_ACCESS='0'
            if request.form.get("cgiAccess"):
                CGI_ACCESS = '1'
            cursor = mysqlconnection.cursor()
            query = "UPDATE `packages` SET  `Package_Name` = '"+Package_Name+"', `Limit_FTP` = '"+Limit_FTP+"', `Limit_Mails` = '"+Limit_Mails+"', `Limit_Domains` = '"+Limit_Domains+"', `CGI_ACCESS` = '"+CGI_ACCESS+"', `Limit_DB` = '"+Limit_DB+"', `Sub_Domains` = '"+Sub_Domains+"', `Storage_Limit` = '"+Storage_Limit+"' WHERE `packages`.`Package_Id` = "+packageID+""
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(request.referrer)
            else:
                return redirect(request.referrer)
        else:
            return redirect(request.referrer)

    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Packages/deletePackage', methods =['GET', 'POST'])
def admin_deletePackage():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('packageID'):
            packageID=request.args.get('packageID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `packages` SET `Is_Active` = '0' WHERE `packages`.`Package_Id` ="+packageID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewPackages"))
            else:
                return redirect(url_for("routes.admin_viewPackages"))

        else:
            return redirect(url_for("routes.admin_viewPackages"))
    else:
        return redirect(url_for('routes.login'))
@routes.route('/admin/domains/addDomain', methods = ['GET', 'POST'])
def admin_addDomain():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `users` where Is_Deleted=0;')
        users = cursor.fetchall()
        if request.method == 'POST' and 'userID' in request.form and 'DomainName' in request.form:
            userID = request.form['userID']
            cursor.execute('SELECT servUser FROM `users` where Is_Deleted=0 and User_id='+userID+';')
            getUserName = cursor.fetchone()[0]
            DomainName = request.form['DomainName']
            query = "INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, '"+DomainName+"', '1', '0', '0');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
                add_vhost(getUserName,DomainName)
            except:
                msg={"error":"danger","message":"Domain Already Added."}
                return render_template('adminFiles/domains/addDomain.html', users=users, msg=msg)
            if cursor.rowcount>0:
                msg={"error":"success","message":"Domain Added."}
                return render_template('adminFiles/domains/addDomain.html', users=users, msg=msg)
            else:
                msg = {"error": "danger", "message": "Domain Not Added."}
                return render_template('adminFiles/domains/addDomain.html', users=users, msg=msg)
        else:
            msg=''
            return render_template('adminFiles/domains/addDomain.html', users=users, msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/domains/viewDomains')
def admin_viewDomains():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        #cursor.execute('SELECT * FROM `users` where Is_Deleted=0;')
        cursor.execute('SELECT * FROM `domains` INNER JOIN users ON domains.User_id = users.User_id where domains.Is_Deleted=0;')
        results = cursor.fetchall()
        return render_template('adminFiles/domains/viewDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domains/updateDomains')
def admin_updateDomains():
    if check_admin_Login():
        msg=''
        if request.method == 'GET' and request.args.get('domainID'):
            domainID=request.args.get('domainID')
            cursor = mysqlconnection.cursor()
            query="select * from domains WHERE `domains`.`Domain_Id` ="+domainID
            cursor.execute(query)
            domain = cursor.fetchone()
            if cursor.rowcount>0:
                if domain[3]==0:
                    query = "UPDATE `domains` SET `Domain_Suspended` = '1' WHERE `domains`.`Domain_Id` =" + domainID
                    cursor.execute(query)
                    mysqlconnection.commit()
                    return redirect(url_for("routes.admin_viewDomains"))
                else:
                    query = "UPDATE `domains` SET `Domain_Suspended` = '0' WHERE `domains`.`Domain_Id` =" + domainID
                    cursor.execute(query)
                    mysqlconnection.commit()
                    return redirect(url_for("routes.admin_viewDomains"))
            else:
                return redirect(url_for("routes.admin_viewDomains"))
        return redirect(url_for("routes.admin_viewDomains"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Packages/deleteDomain', methods =['GET', 'POST'])
def admin_deleteDomain():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('domainID'):
            domainID=request.args.get('domainID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `domains` SET `Is_Deleted` = '1' WHERE `domains`.`Domain_Id` ="+domainID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewDomains"))
            else:
                return redirect(url_for("routes.admin_viewDomains"))

        else:
            return redirect(url_for("routes.admin_viewDomains"))
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Databases/addDB', methods = ['GET','POST'])
def admin_addDB():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `users` where Is_Deleted=0;')
        users = cursor.fetchall()
        if request.method == 'POST' and 'userID' in request.form and 'databaseName' in request.form:
            userID = request.form['userID']
            cursor.execute('SELECT * FROM `mysqldbusers` INNER JOIN users ON mysqldbusers.User_id = users.User_id where Is_Deleted=0 and users.User_id='+userID+';')
            DBUserbyID = cursor.fetchone()

            #print(DBUserbyID[0])
            databaseName = request.form['databaseName']
            query = "INSERT INTO `msqldatabases` (`DB_ID`, `DbName`, `User_id`, `DbUser_ID`, `Is_Active`) VALUES (NULL, '"+databaseName+"', '"+userID+"', '"+str(DBUserbyID[0])+"', '1');"
            #query = "INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES (NULL, '"+DomainName+"', '1', '0', '0');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg={"error":"danger","message":"Database name already in use."}
                return render_template('adminFiles/MysqlDatabase/addDB.html', users=users, msg=msg)
            if cursor.rowcount>0:
                msg={"error":"success","message":"Database Added.."}
                return render_template('adminFiles/MysqlDatabase/addDB.html', users=users, msg=msg)
            else:
                msg = {"error": "danger", "message": "Database Adding not Successfull."}
                return render_template('adminFiles/MysqlDatabase/addDB.html', users=users, msg=msg)
        else:
            msg=''
            return render_template('adminFiles/MysqlDatabase/addDB.html', users=users, msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Databases/MysqlDatabase/viewDatabases')
def admin_viewDatabases():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM mysqldbusers LEFT JOIN msqldatabases ON msqldatabases.DbUser_ID = mysqldbusers.DbUser_ID LEFT JOIN users ON users.User_id = mysqldbusers.User_id WHERE msqldatabases.Is_Active = 1')
        results = cursor.fetchall()
        msg = ''
        return render_template('adminFiles/MysqlDatabase/viewDatabases.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Databases/deleteDatabase', methods =['GET', 'POST'])
def admin_deleteDatabase():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('DbID'):
            DbID=request.args.get('DbID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `msqldatabases` SET `Is_Active` = '0' WHERE `msqldatabases`.`DB_ID` = "+DbID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewDatabases"))
            else:
                return redirect(url_for("routes.admin_viewDatabases"))

        else:
            return redirect(url_for("routes.admin_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))



@routes.route('/admin/Databases/updateDBPass', methods=['GET', 'POST'])
def admin_updateDBPass():
    if check_admin_Login():
        msg=''
        if request.method == 'GET' and request.args.get('DbID'):
            DbUser_ID=request.args.get('DbID')
            cursor = mysqlconnection.cursor()
            query="SELECT * FROM `mysqldbusers` WHERE `mysqldbusers`.`DbUser_ID` ="+DbUser_ID
            cursor.execute(query)
            database = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=database[0])
            else:
                return redirect(url_for("routes.admin_viewDatabases"))
        elif request.method == 'POST' and 'DbID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            DbUser_ID = request.form['DbID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                query = "UPDATE `mysqldbusers` SET `DbPassword` = '"+EncodedPassword+"' WHERE `mysqldbusers`.`DbUser_ID` = "+DbUser_ID+""
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    msg = {"error": "success", "message": "Database Password Updated."}
                    return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('adminFiles/MysqlDatabase/updateDBPass.html', database=DbUser_ID, msg=msg)
        else:
            return redirect(url_for("routes.admin_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/addAccounts', methods=['GET', 'POST'])
def admin_addAccounts():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `users` where Is_Deleted=0;')
        users = cursor.fetchall()
        if request.method == 'POST' and 'userID' in request.form and 'ftpUsername' in request.form and 'ftpPassword' in request.form :
            userID = request.form['userID']
            ftpUsername = request.form['ftpUsername']
            ftpPassword = request.form['ftpPassword']
            encodedPass = Base64Encode(ftpPassword)
            #ftpPassword = request.form['ftpPassword']
            Directory = "/home/username/public_html"
            query = "INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES (NULL, '"+userID+"', '"+Directory+"', '"+ftpUsername+"', '"+encodedPass+"', '1');"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg={"error":"danger","message":"FTP Username Already in Use."}
                return render_template('adminFiles/ftpAccounts/addAccounts.html', users=users, msg=msg)
            if cursor.rowcount>0:
                msg={"error":"success","message":"FTP Account Added."}
                return render_template('adminFiles/ftpAccounts/addAccounts.html', users=users, msg=msg)
            else:
                msg = {"error": "danger", "message": "FTP account not added."}
                return render_template('adminFiles/ftpAccounts/addAccounts.html', users=users, msg=msg)
        else:
            msg=''
            return render_template('adminFiles/ftpAccounts/addAccounts.html', users=users, msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/viewAccounts')
def admin_viewAccounts():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `ftp_accounts` INNER JOIN users ON ftp_accounts.User_id = users.User_id where ftp_accounts.Is_Active=1;')
        results = cursor.fetchall()
        msg = ''
        return render_template('adminFiles/ftpAccounts/viewAccounts.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/FTPAccounts/updateAccountPass', methods=['GET', 'POST'])
def admin_updateAccountPass():
    if check_admin_Login():
        msg=''
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')
            cursor = mysqlconnection.cursor()
            query="SELECT * FROM `ftp_accounts` where Account_Id="+AccID
            cursor.execute(query)
            account = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('adminFiles/ftpAccounts/updateAccountPass.html', account=account[0])
            else:
                return redirect(url_for("routes.admin_viewAccounts"))
        elif request.method == 'POST' and 'AccID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            AccID = request.form['AccID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                query = "UPDATE `ftp_accounts` SET `FTP_Password` = '"+EncodedPassword+"' WHERE `ftp_accounts`.`Account_Id` = "+AccID+""
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount>0:
                    msg = {"error": "success", "message": "FTP Account Password Updated."}
                    return render_template('adminFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
                else:
                    msg = {"error": "danger", "message": "Password not Updated"}
                    return render_template('adminFiles/ftpAccounts/updateAccountPass.html', account=AccID, msg=msg)
            else:
                msg = {"error": "danger", "message": "Password and confirm password does not match."}
                return render_template('adminFiles/ftpAccounts/updateAccountPass.html', database=AccID, msg=msg)
        else:
            return redirect(url_for("routes.admin_viewDatabases"))
    else:
        return redirect(url_for('routes.login'))



@routes.route('/admin/FTPAccounts/deleteAccount', methods =['GET', 'POST'])
def admin_deleteAccount():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('AccID'):
            AccID=request.args.get('AccID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `ftp_accounts` SET `Is_Active` = '0' WHERE `ftp_accounts`.`Account_Id` = "+AccID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewAccounts"))
            else:
                return redirect(url_for("routes.admin_viewAccounts"))

        else:
            return redirect(url_for("routes.admin_viewAccounts"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/ftpServer')
def admin_ftpServer():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/ftpAccounts/ftpServer.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/addEmail', methods=['GET','POST'])
def admin_addEmail():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0;')
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form and 'Password' in request.form :
            domainID = request.form['domainID']
            suffix = request.form['suffix']
            Password = request.form['Password']
            encodedPass = Base64Encode(Password)
            query= "SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id="+domainID+""
            cursor.execute(query)
            rDomain = cursor.fetchone()
            mail_adress= suffix+"@"+rDomain[1]
            userID= str(rDomain[2])
            query = "INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES (NULL, '"+domainID+"', '"+userID+"', '"+mail_adress+"', '"+encodedPass+"', '1')"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg={"error":"danger","message":"Mail Account Already Exists."}
                return render_template('adminFiles/Mails/addEmail.html', domains=domains, msg=msg)
            if cursor.rowcount>0:
                msg={"error":"success","message":"Mail Account Added."}
                return render_template('adminFiles/Mails/addEmail.html', domains=domains, msg=msg)
            else:
                msg = {"error": "danger", "message": "Mail Account not added."}
                return render_template('adminFiles/Mails/addEmail.html', domains=domains, msg=msg)
        else:
            msg=''
            return render_template('adminFiles/Mails/addEmail.html', domains=domains, msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/viewEmail')
def admin_viewEmail():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM mail_accounts LEFT JOIN users ON users.User_id = mail_accounts.User_id LEFT JOIN domains ON domains.Domain_Id = mail_accounts.Domain_Id WHERE mail_accounts.Is_Active = 1')
        results = cursor.fetchall()
        msg = ''
        return render_template('adminFiles/Mails/viewEmail.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/deleteEmail', methods =['GET', 'POST'])
def admin_deleteEmail():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('mailID'):
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `mail_accounts` SET `Is_Active` = '0' WHERE `mail_accounts`.`Mail_Id` = "+mailID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewEmail"))
            else:
                return redirect(url_for("routes.admin_viewEmail"))

        else:
            return redirect(url_for("routes.admin_viewEmail"))
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/EmailAccounts/updateEmail', methods=['GET', 'POST'])
def admin_updateEmail():
    if check_admin_Login():
        msg=''
        if request.method == 'GET' and request.args.get('mailID'):
            mailID=request.args.get('mailID')
            cursor = mysqlconnection.cursor()
            query="SELECT * FROM `mail_accounts` where Mail_Id="+mailID
            cursor.execute(query)
            mail = cursor.fetchone()
            if cursor.rowcount>0:
                return render_template('adminFiles/Mails/updateEmail.html', mail=mail[0])
            else:
                return redirect(url_for("routes.admin_viewEmail"))
        elif request.method == 'POST' and 'mailID' in request.form and 'pass1' in request.form and 'pass2' in request.form:
            mailID = request.form['mailID']
            pass1 = request.form['pass1']
            pass2 = request.form['pass2']
            if pass1 == pass2:
                EncodedPassword = Base64Encode(pass1)
                cursor = mysqlconnection.cursor()
                query = "UPDATE `mail_accounts` SET `Mail_Pass` = '"+EncodedPassword+"' WHERE `mail_accounts`.`Mail_Id` = "+mailID+""
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount>0:
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
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM `domains` where Is_Deleted=0;')
        domains = cursor.fetchall()
        if request.method == 'POST' and 'domainID' in request.form and 'suffix' in request.form :
            domainID = request.form['domainID']
            suffix = request.form['suffix']
            query= "SELECT * FROM `domains` where Is_Deleted=0 and Domain_Id="+domainID+""
            cursor.execute(query)
            rDomain = cursor.fetchone()
            SubDomainAdress= suffix+"."+rDomain[1]
            userID= str(rDomain[2])
            query = "INSERT INTO `subdomains` (`SDomain_ID`, `Domain_Id`, `User_id`, `SubDomain`, `Is_Active`) VALUES (NULL, '"+domainID+"', '"+userID+"', '"+SubDomainAdress+"', '1')"
            try:
                cursor.execute(query)
                mysqlconnection.commit()
            except:
                msg={"error":"danger","message":"Subdomain Already Exists."}
                return render_template('adminFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            if cursor.rowcount>0:
                msg={"error":"success","message":"Subdomain Added."}
                return render_template('adminFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
            else:
                msg = {"error": "danger", "message": "Subdomain not added."}
                return render_template('adminFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
        else:
            msg=''
            return render_template('adminFiles/SubDomains/addSubDomain.html', domains=domains, msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/SubDomains/viewSubDomains')
def admin_viewSubDomains():
    if check_admin_Login():
        cursor = mysqlconnection.cursor()
        cursor.execute('SELECT * FROM subdomains LEFT JOIN users ON users.User_id = subdomains.User_id LEFT JOIN domains ON domains.Domain_Id = subdomains.Domain_Id WHERE subdomains.Is_Active = 1')
        results = cursor.fetchall()
        msg = ''
        return render_template('adminFiles/SubDomains/viewSubDomains.html', results=results)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/SubDomains/deleteSubdomain', methods =['GET', 'POST'])
def admin_deleteSubDomain():
    if check_admin_Login():
        if request.method == 'GET' and request.args.get('SdomainID'):
            SdomainID=request.args.get('SdomainID')
            cursor = mysqlconnection.cursor()
            query="UPDATE `subdomains` SET `Is_Active` = '0' WHERE `subdomains`.`SDomain_ID` = "+SdomainID
            cursor.execute(query)
            mysqlconnection.commit()
            if cursor.rowcount>0:
                return redirect(url_for("routes.admin_viewSubDomains"))
            else:
                return redirect(url_for("routes.admin_viewSubDomains"))

        else:
            return redirect(url_for("routes.admin_viewSubDomains"))
    else:
        return redirect(url_for('routes.login'))





@routes.route('/admin/Logs/error_Logs')
def admin_error_logs():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/Logs/error_logs.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/Logs/access_logs')
def admin_access_logs():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/Logs/access_logs.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))
