from flask import render_template, request,redirect, url_for
from Database.DbConfig import mysqlconnection

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
        msg=''
        return render_template('adminFiles/users/viewUser.html', msg=msg)
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
        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            cursor = mysqlconnection.cursor()
            #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
            cursor.execute('UPDATE `administrator` SET `Admin_Name` = %s WHERE Admin_id = %s;', (Name,session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                session["Name"]=Name;
                return render_template('adminFiles/users/addUser.html', msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('adminFiles/users/addUser.html', msg={"error":"primary","message":"Name not Updated."})

        else:
            return render_template('adminFiles/users/addUser.html')
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/users/updateUser')
def admin_updateUser():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/users/updateUser.html', msg=msg)
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
