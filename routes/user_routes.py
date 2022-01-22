from flask import render_template, session
from . import routes
from app import *
import functions

@routes.route('/user/dashboard')
def user_dashboard():
    if check_user_Login():
        msg=''
        return render_template('userFiles/dashboard.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/user/profile')
def user_profile():
    if check_user_Login():
        msg=''
        return render_template('userFiles/profile.html', msg=msg)
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
