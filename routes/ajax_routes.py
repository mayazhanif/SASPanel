from flask import render_template
from app import app
from . import routes
from app import *
from Database.DbConfig import mysqlconnection
from cachelib import SimpleCache
import json


@routes.route('/UpdateDashboard')
def UpdateDashboard():
    if check_admin_Login() or check_user_Login():
        Result = GetAllInfo()
        response = app.response_class(
            response=json.dumps(Result),
                status=200,
                mimetype='application/json'
        )
        return response
    else:
        return redirect(url_for('routes.login'))