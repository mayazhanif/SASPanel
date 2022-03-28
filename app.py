import re
import os
from flask import Flask, render_template, request, redirect, url_for, session
from routes.admin_routes import *
from routes.login_routes import *
from routes.custom_pages import *
from routes.user_routes import *
from functions import *
app = Flask(__name__,
            static_url_path='',
            static_folder='apps/static',
            template_folder='apps/templates')
app.register_blueprint(routes)
app.secret_key = 'SecRET@Key123'
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=int("5000"), debug=True)

