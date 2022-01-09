from flask import render_template
from . import routes
from app import *


@routes.route('/dashboard')
def user_dashboard():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)


@routes.route('/profile')
def user_profile():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)


@routes.route('/domains/addnew')
def user_add_domain():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)


@routes.route('/users')
def user_users():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)
