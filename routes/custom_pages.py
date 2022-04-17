from flask import render_template
from app import app
from . import routes
from app import *
from Database.DbConfig import mysqlconnection


@routes.route('/test/')
def hello_world():  # put application's code here
    msg='<p style="text-align: center; "><b>Password Reset</b></p><p style="text-align: center; ">Open This Link to Reset Your Password</p><p style="text-align: center; "><a href="https://pythonbasics.org/flask-mail/#Flask-mail-example" target="_blank"><span style="font-family: &quot;Arial Black&quot;;">Click here</span></a><br></p>'
    mailSender("Password Reset","mayazhanif@gmail.com",msg,"HTML")
    return "Sent"


@routes.route('/installer')
def installer():
    install()
    return render_template('installer/installer.html')


@routes.route('/')
def home_route():  # put application's code here
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
