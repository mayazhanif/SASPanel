from flask import render_template
from . import routes


@routes.route('/dashboard')
def user_dashboard():
    msg=''
    return render_template('userFiles/dashboard.html', msg=msg)
