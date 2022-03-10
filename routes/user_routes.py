from flask import render_template, session, request, redirect, url_for
from . import routes
from app import *
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
        if request.method == 'POST' and 'Name' in request.form:
            Name = request.form['Name']
            cursor = mysqlconnection.cursor()
            #cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            #print("UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id'])")
            cursor.execute('UPDATE `users` SET `User_Name` = %s WHERE User_id = %s;', (Name,session['id']))
            mysqlconnection.commit()
            if cursor.rowcount>0:
                session["Name"]=Name;
                return render_template('userFiles/profile.html', msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('userFiles/profile.html', msg={"error":"primary","message":"Name not Updated."})

        else:
            return render_template('userFiles/profile.html') 
    else:
        return redirect(url_for('routes.login'))



@routes.route('/user/domains/addDomain')
def user_addDomain():
    if check_user_Login():
        msg=''
        return render_template('userFiles/domains/addDomain.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/domains/viewDomains')
def user_viewDomains():
    if check_user_Login():
        msg=''
        return render_template('userFiles/domains/viewDomains.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/domains/updateDomains')
def user_updateDomains():
    if check_user_Login():
        msg=''
        return render_template('userFiles/domains/updateDomains.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Databases/addDBUser')
def user_addDBUser():
    if check_user_Login():
        msg=''
        return render_template('userFiles/MysqlDatabase/addDBUser.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Databases/addDB')
def user_addDB():
    if check_user_Login():
        msg=''
        return render_template('userFiles/MysqlDatabase/addDB.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/Databases/MysqlDatabase/viewDatabases')
def user_viewDatabases():
    if check_user_Login():
        msg=''
        return render_template('userFiles/MysqlDatabase/viewDatabases.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/addAccounts')
def user_addAccounts():
    if check_user_Login():
        msg=''
        return render_template('userFiles/ftpAccounts/addAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/viewAccounts')
def user_viewAccounts():
    if check_user_Login():
        msg=''
        return render_template('userFiles/ftpAccounts/viewAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))


@routes.route('/user/FTPAccounts/updateAccounts')
def user_updateAccounts():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/ftpAccounts/updateAccounts.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/FTPAccounts/ftpServer')
def user_ftpServer():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/ftpAccounts/ftpServer.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/EmailAccounts/addEmail')
def user_addEmail():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/Mails/addEmail.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/EmailAccounts/viewEmail')
def user_viewEmail():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/Mails/viewEmail.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/EmailAccounts/updateEmail')
def user_updateEmail():
    if check_user_Login():
        msg = ''
        return render_template('userFiles/Mails/updateEmail.html', msg=msg)
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

