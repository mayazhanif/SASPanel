from flask import flash, request, redirect, url_for
from Database.DbConfig import mysqlconnection
from app import *
from functions import *
import hashlib
from routes import routes

@routes.route('/login/', methods=['GET', 'POST'])
def login(msg=""):
    #check_user_Login()
    if request.method == 'POST' and 'Email' in request.form and 'password' in request.form and 'logintype' in request.form:
        Email = request.form['Email']
        password = request.form['password']
        md5password = hashlib.md5(password.encode()).hexdigest()
        logintype = request.form['logintype']
        if logintype == "Admin":
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT * FROM administrator WHERE Admin_Email = %s AND Admin_Password = %s', (Email, md5password))
            result = cursor.fetchone()
            if result==None:
                #return redirect(url_for('routes.login'))
                #flash('You were successfully logged in')
                return render_template('authentication/login.html', msg={"error":"primary","message":"Invalid email or password."})
            else:
                session['usertype'] = "Admin"
                session['loggedin'] = True
                session['id'] = result[0]
                session['Email'] = result[4]
                session['Name'] = result[1]
                return redirect(url_for('routes.admin_dashboard'))
            #return render_template('authentication/login.html', msg="Error")
        elif logintype == "User":
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            result = cursor.fetchone()
            #print(result)
            if result==None:
                #return redirect(url_for('routes.login'))
                #flash('You were successfully logged in')
                return render_template('authentication/login.html',msg={"error":"primary","message":"Invalid email or password."})
            else:
                session['usertype'] = "User"
                session['loggedin'] = True
                session['id'] = result[0]
                session['Email'] = result[2]
                session['Name'] = result[4]
                session['servUser'] = result[1]
                return redirect(url_for('routes.user_dashboard'))
        else:
            return render_template('authentication/login.html', msg={"error":"primary","message":"Please fill all fields Correctly."})
    return render_template('authentication/login.html',title="Login")

@routes.route('/forgot/', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        return render_template('authentication/forgot-password.html',
                               msg=True)
    else:
        return render_template('authentication/forgot-password.html', msg=False)

@routes.route('/logout/', methods=['GET', 'POST'])
def logout():
    msg=''
    session.pop('loggedin', None)
    session.pop('usertype', None)
    session.pop('id', None)
    return redirect(url_for('routes.login'))
