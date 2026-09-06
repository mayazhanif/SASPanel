from flask import redirect, url_for, jsonify, request, session
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


@routes.route('/ajax/domains_by_user')
def ajax_domains_by_user():
    """Return active domains for a specific user, scoped to the logged-in admin.
    Query param: user_id (int)
    Returns: JSON list of {id, domain} objects, or {error: str} on failure.
    """
    if not check_admin_Login():
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = request.args.get('user_id', '')
    if not user_id or not user_id.isdigit():
        return jsonify([])
    try:
        mysqlconnection.reconnect()
        cursor = mysqlconnection.cursor()
        # Scope: domain must belong to this admin's user (IDOR guard)
        cursor.execute(
            'SELECT Domain_Id, Domain_Name FROM `domains` '
            'WHERE Is_Deleted=0 '
            'AND User_id=%s '
            'AND User_id IN (SELECT User_id FROM users WHERE Admin_id=%s AND Is_Deleted=0)',
            (user_id, str(session['id']))
        )
        rows = cursor.fetchall()
        return jsonify([{'id': r[0], 'domain': r[1]} for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500