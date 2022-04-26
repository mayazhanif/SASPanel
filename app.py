import re
import os
from flask import Flask, render_template, request, redirect, url_for, session
from routes.admin_routes import *
from routes.login_routes import *
from routes.custom_pages import *
from routes.user_routes import *
from routes.ajax_routes import *
from functions import *
from flask_mail import Mail, Message

app = Flask(__name__,
            static_url_path='',
            static_folder='apps/static',
            template_folder='apps/templates')
app.register_blueprint(routes)
app.secret_key = 'SecRET@Key123'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAIL_SERVER']='185.162.10.153'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = 'support@saspanel.org'
app.config['MAIL_PASSWORD'] = 'support'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
@app.after_request
def add_header(r):
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'no-store'
    return r
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=int("5000"), debug=True)

