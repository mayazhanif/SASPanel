from flask import render_template, session, request, redirect
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



@routes.route('/user/domains/addnew')
def user_add_domain():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)


@routes.route('/users')
def user_users():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)
