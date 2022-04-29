from flask import render_template
from app import app
from . import routes
from app import *
from Database.DbConfig import mysqlconnection,mysql_reconnect


@routes.route('/test/')
def hello_world():
    print(mysqlconnection)
    mysql_reconnect()
    print(mysqlconnection)
    print(generateservUser("testuser","testuser@gmail.com"))
    return "Sent"


@routes.route('/installer', methods=['POST','GET'])
def installer():
    msg=''
    if request.method == 'POST' and 'DBpass1' in request.form and 'DBpass2' in request.form and 'mailserverpassword' in request.form and 'emailaddress' in request.form and 'domain' in request.form and 'emailpassword' in request.form and mysqlconnection is None:
        #install()
        DBpass1 = request.form['DBpass1']
        DBpass2 = request.form['DBpass2']
        mailserverpassword = request.form['mailserverpassword']
        emailaddress = request.form['emailaddress']
        emailpassword = request.form['emailpassword']
        domain = request.form['domain']
        if DBpass1 == DBpass2:
            emailaddress=emailaddress+"@"+domain
            install_packages(DBpass1,mailserverpassword,domain,emailaddress,emailpassword)
            return render_template('installer/installer.html',msg={"error": "success", "message": "Installation Completed. Please Reload."})
        else:
            print("Password and Confirm Password Mismatch.")
            return render_template('installer/installer.html',
                                   msg={"error": "danger", "message": "Password and Confirm Password Mismatch."})
    elif mysqlconnection is None:
        return render_template('installer/installer.html')
    else:
        #print(mysqlconnection)
        return render_template('installer/installed.html')


@routes.route('/')
def home_route():
    if mysqlconnection is None:
        return redirect(url_for('routes.installer'))
    if 'loggedin' in session:
        print(session['usertype'])
        if session['usertype'] == "Admin":
            msg = ''
            return redirect(url_for('routes.admin_dashboard'))
        elif session['usertype'] == "User":
            msg = ''
            return redirect(url_for('routes.user_dashboard'))
    else:
        msg = 'Please, Login first.'
        return redirect(url_for('routes.login'))


@routes.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error_pages/404.html'), 404


@routes.errorhandler(500)
def page_not_found(e):
    # note that we set the 500 status explicitly
    return render_template('error_pages/500.html'), 404
