from flask import session, render_template
import random
import string
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

def generateservUser(name, email):
    num = str(random.randint(0, 999))
    uname = name[3] + email[:7] + num
    return uname

def generatePassword():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(8))
    return password