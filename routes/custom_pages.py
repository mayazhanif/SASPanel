from flask import render_template
from . import routes


@routes.route('/test/')
def hello_world():  # put application's code here
    return 'Hello World!'


@routes.route('/')
def home_route():  # put application's code here
    msg = ''
    return render_template('adminFiles/dashboard.html', msg=msg)


@routes.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error_pages/404.html'), 404


@routes.errorhandler(500)
def page_not_found(e):
    # note that we set the 500 status explicitly
    return render_template('error_pages/500.html'), 404
