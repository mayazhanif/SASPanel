from flask import flash, request, redirect, url_for
from Database.DbConfig import mysqlconnection
from app import *
from functions import *
import hashlib
from routes import routes
import secrets
from datetime import date
@routes.route('/login/', methods=['GET', 'POST'])
def login(msg=""):
    mysqlconnection.reconnect()
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
                return render_template('authentication/login.html', msg={"error":"primary","message":"Invalid email or password."})
            else:
                session['usertype'] = "Admin"
                session['loggedin'] = True
                session['id'] = result[0]
                session['Email'] = result[4]
                session['Name'] = result[1]
                return redirect(url_for('routes.admin_dashboard'))
        elif logintype == "User":
            cursor = mysqlconnection.cursor()
            cursor.execute('SELECT * FROM users WHERE User_email = %s AND User_Password = %s', (Email, md5password))
            result = cursor.fetchone()
            #print(result)
            if result==None:
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
    mysqlconnection.reconnect()
    if request.method == 'POST' and 'Email' in request.form:
        Email = request.form['Email']
        cursor = mysqlconnection.cursor()
        cursor.execute("SELECT User_id,User_email FROM users WHERE User_email = '"+Email+"' and Is_Deleted=0")
        result = cursor.fetchone()
        if result == None:
            return render_template('authentication/forgot-password.html', reset=True)
        else:
            userID = str(result[0])
            userEmail = result[1]
            today = date.today()
            Token = secrets.token_urlsafe()
            query = "UPDATE `users` SET `UserResetToken` = '"+Token+"', Token_Expiry=CURRENT_TIMESTAMP WHERE `users`.`User_id` = "+userID+";"
            cursor.execute(query)
            o = urlparse(request.base_url)
            mainhost = o.hostname+":"+str(o.port)
            url = 'http://'+mainhost+'/reset?token=' + Token
            print(url)
            msg = '<p style="text-align: center; "><b>Password Reset</b></p><p style="text-align: center; ">Open This Link to Reset Your Password</p><p style="text-align: center; "><a href="'+url+'" target="_blank"><span style="font-family: &quot;Arial Black&quot;;">Click here</span></a><br></p>'
            #mailSender("Password Reset", userEmail, msg, "HTML")
            return render_template('authentication/forgot-password.html', reset=True)
    else:
        return render_template('authentication/forgot-password.html', reset=False)

@routes.route('/reset/', methods=['GET', 'POST'])
def reset_password():
    mysqlconnection.reconnect()
    if request.method == 'GET' and request.args.get('token'):
        cursor = mysqlconnection.cursor()
        token = request.args.get('token')
        cursor.execute("SELECT Token_Expiry FROM users WHERE UserResetToken = '"+token+"' and Is_Deleted=0")
        result = cursor.fetchone()
        if result == None:
            return render_template('authentication/forgot-password.html', reset=False,
                                   msg={"error": "danger", "message": "Reset Token Expired or Mismatch."})
        else:
            Tokenexpiry = result[0]
            Now = datetime.today()
            Different = Now - Tokenexpiry
            Difference = Different.total_seconds() / 60
            if Difference>59:
                return render_template('authentication/forgot-password.html', reset=False, msg={"error":"danger","message":"Reset Token Expired."})
            else:
                return render_template('authentication/reset-password.html', token=token, reset=False)
    elif request.method == 'POST' and 'pass1' in request.form and 'pass2' in request.form and 'token' in request.form:
        pass1 = request.form['pass1']
        pass2 = request.form['pass2']
        token = request.form['token']
        if pass1 == pass2:
            cursor = mysqlconnection.cursor()
            md5Password = md5encode(pass1)
            cursor.execute('UPDATE `users` SET `User_Password` = %s WHERE UserResetToken = %s;',
                           (md5Password, token))
            mysqlconnection.commit()
            if cursor.rowcount > 0:
                query= "UPDATE `users` SET `UserResetToken` = '' WHERE UserResetToken = '"+token+"';"
                cursor.execute(query)
                mysqlconnection.commit()
                return render_template('authentication/forgot-password.html', reset=False,
                                       msg={"error": "success", "message": "Password Change Successful."})
            else:
                return render_template('authentication/forgot-password.html', reset=False,
                                       msg={"error": "primary", "message": "Password not Updated."})
        else:
            return render_template('authentication/forgot-password.html', reset=False,
                                   msg={"error": "danger", "message": "Password and Confirm Password Mismatch."})
    else:
        return render_template('authentication/forgot-password.html', reset=False)
@routes.route('/logout/', methods=['GET', 'POST'])
def logout():
    msg=''
    session.pop('loggedin', None)
    session.pop('usertype', None)
    session.pop('id', None)
    return redirect(url_for('routes.login'))
