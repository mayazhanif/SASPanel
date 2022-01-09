import re
import os
from flask import Flask, render_template, request, redirect, url_for, session
from routes.admin_routes import *
from routes.login_routes import login

app = Flask(__name__,
            static_url_path='',
            static_folder='apps/static',
            template_folder='apps/templates')
app.register_blueprint(routes)


@app.route('/admin/home', methods=['GET', 'POST'])
def admin_home():
    # Output message if something goes wrong...
    msg = ''
    return render_template('layout/admin/home.html', msg=msg)


@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    # Output message if something goes wrong...
    msg = ''
    return render_template('admin/users.html', msg=msg)


@app.route('/test')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/dashboard')
def dashboard():  # put application's code here
    msg = ''
    return render_template('adminFiles/dashboard.html', msg=msg)


if __name__ == '__main__':
    app.run()
