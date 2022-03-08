from flask import session, render_template

from Database.DbConfig import mysqlconnection


def check_Session(type="User"):
    if 'loggedin' in session:
        if session["usertype"] == type:
            return True
    else:
        return False

def check_user_Login():
    if check_Session("User"):
        return True
    else:
        #print("Redirecting")
        return False

def check_admin_Login():
    if check_Session("Admin"):
        return True
    else:
        #print("Redirecting")
        return False