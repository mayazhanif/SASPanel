from flask import render_template
from . import routes


@routes.route('/admindashboard')
def admin_dashboard():
    msg=''
    return render_template('adminFiles/dashboard.html', msg=msg)


@routes.route('/admin/userslist')
def admin_userslist():
    msg=''
    return render_template('adminFiles/userslist.html', msg=msg)
