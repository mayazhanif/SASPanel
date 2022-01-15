from flask import flash

from Database.DbConfig import mysqlconnection
from app import *


@routes.route('/login/', methods=['GET', 'POST'])
def login(msg=""):
    if request.method == 'POST' and 'Email' in request.form and 'password' in request.form and 'logintype' in request.form:
        Email = request.form['Email']
        password = request.form['password']
        logintype = request.form['logintype']
        if logintype == "Admin":
            #session['usertype'] = "Admin"
            return redirect(url_for('routes.admin_dashboard'))
        elif logintype == "User":
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, password))
            result = cursor.fetchone()
            #print(result)
            if result==None:
                #return redirect(url_for('routes.login'))
                #flash('You were successfully logged in')
                return render_template('authentication/login.html', msg="Error")
            else:
                session['usertype'] = "Admin"
                session['loggedin'] = True
                session['id'] = 1
                session['username'] = Email
                return redirect(url_for('routes.user_dashboard'))
        else:
            return render_template('authentication/login.html', msg="Error")
    return render_template('authentication/login.html',title="Login")


@routes.route('/logout/', methods=['GET', 'POST'])
def logout():
    msg=''
    session.pop('loggedin', None)
    session.pop('usertype', None)
    session.pop('id', None)
    return redirect(url_for('routes.login'))
