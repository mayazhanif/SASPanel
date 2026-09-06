from flask import redirect, url_for, jsonify
from . import routes
from Database.DbConfig import mysqlconnection
from cachelib import SimpleCache
from functions import check_admin_Login, check_user_Login, GetAllInfo


@routes.route('/get_updates')
def get_updates():
    mysqlconnection.reconnect()
    if check_admin_Login() or check_user_Login():
        result = GetAllInfo()
        return jsonify(result)
    else:
        return redirect(url_for('routes.login'))