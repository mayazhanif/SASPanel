from Database.DbConfig import mysqlconnection
from app import *


@routes.route('/login/', methods=['GET', 'POST'])
def login():
    #print(session['id']);
    #username = request.form['username']
    #print(mysqlconnection)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'logintype' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        logintype = request.form['logintype']
        session['loggedin'] = True
        session['id'] = 1
        session['username'] = username
        #session['usertype'] = request.form['logintype']
        if logintype == "Admin":
            session['usertype'] = "Admin"
            return redirect(url_for('routes.admin_dashboard'))
        elif logintype == "User":
            session['usertype'] = "User"
            return redirect(url_for('routes.user_dashboard'))
        else:
            return render_template('authentication/login.html', msg="Error")
        # Check if account exists using MySQL
        cursor = mysqlconnection.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
                # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            return ""
            # Account doesnt exist or username/password incorrect
            #flash("Incorrect username/password!", "danger")
    return render_template('authentication/login.html',title="Login")


@routes.route('/logout/', methods=['GET', 'POST'])
def logout():
    msg=''
    session.pop('loggedin', None)
    session.pop('usertype', None)
    session.pop('id', None)
    return redirect(url_for('routes.login'))
