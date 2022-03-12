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
        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            cursor = mysqlconnection.cursor()
            #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
            cursor.execute('UPDATE `administrator` SET `Admin_Name` = %s WHERE Admin_id = %s;', (Name,session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                session["Name"]=Name;
                return render_template('adminFiles/profile.html', msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('adminFiles/profile.html', msg={"error":"primary","message":"Name not Updated."})

        else:
            return render_template('adminFiles/profile.html')
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
                cursor = mysqlconnection.cursor()
                # query = "INSERT INTO `packages` (`Package_Id`, `Package_Name`, `Admin_id`, `Limit_FTP`, `Limit_Mails`, `Limit_Domains`, `CGI_ACCESS`, `Limit_DB`, `Sub_Domains`, `Storage_Limit`) VALUES (NULL, '"+Package_Name+"', '"+Admin_id+"', '"+Limit_FTP+"', '"+Limit_Mails+"', '"+Limit_Domains+"', '"+CGI_ACCESS+"', '"+Limit_DB+"', '"+Sub_Domains+"', '"+Storage_Limit+"');"
                query = "INSERT INTO `users` (`User_id`, `User_email`, `User_Password`, `User_Name`, `UserResetToken`, `Token_Expiry`, `Admin_id`, `Package_id`, `Is_Deleted`, `User_Reg_Date`) VALUES (NULL, '" + User_email + "', '" + md5Password + "', '" + User_Name + "', '', CURRENT_TIMESTAMP, '" + Admin_id + "', '" + packageID + "', '0', CURRENT_TIMESTAMP);"
                cursor.execute(query)
                mysqlconnection.commit()
                if cursor.rowcount > 0:
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
@routes.route('/admin/domains/addDomain')
def admin_addDomain():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/domains/addDomain.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/domains/viewDomains')
def admin_viewDomains():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/domains/viewDomains.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domains/updateDomains')
def admin_updateDomains():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/domains/updateDomains.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Databases/addDBUser')
def admin_addDBUser():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/MysqlDatabase/addDBUser.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Databases/addDB')
def admin_addDB():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/MysqlDatabase/addDB.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/Databases/MysqlDatabase/viewDatabases')
def admin_viewDatabases():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/MysqlDatabase/viewDatabases.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/addAccounts')
def admin_addAccounts():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/ftpAccounts/addAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/viewAccounts')
def admin_viewAccounts():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/ftpAccounts/viewAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/FTPAccounts/updateAccounts')
def admin_updateAccounts():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/ftpAccounts/updateAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/FTPAccounts/ftpServer')
def admin_ftpServer():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/ftpAccounts/ftpServer.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/addEmail')
def admin_addEmail():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/Mails/addEmail.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/viewEmail')
def admin_viewEmail():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/Mails/viewEmail.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/EmailAccounts/updateEmail')
def admin_updateEmail():
    if check_admin_Login():
        msg = ''
        return render_template('adminFiles/Mails/updateEmail.html', msg=msg)
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
