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
        return render_template('adminFiles/viewUser.html', msg=msg)
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
                return render_template('adminFiles/addUser.html', msg={"error":"success","message":"Name Updated Successfully."})
            else:
                return render_template('adminFiles/addUser.html', msg={"error":"primary","message":"Name not Updated."})

        else:
            return render_template('adminFiles/addUser.html')
    else:
        return redirect(url_for('routes.login'))


@routes.route('/admin/users/updateUser')
def admin_updateUser():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/updateUser.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/domains/addDomain')
def admin_addDomain():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/addDomain.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))