from flask import render_template
from . import routes
from functions import *


@routes.route('/admin/dashboard')
def admin_dashboard():
    if check_admin_Login():
        msg=''
        return render_template('adminFiles/dashboard.html', msg=msg)
    else:
        return redirect(url_for('routes.login'))

@routes.route('/admin/userslist')
def admin_userslist():
    msg=''
    return render_template('adminFiles/userslist.html', msg=msg)
