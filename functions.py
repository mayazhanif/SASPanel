import base64
import hashlib
import re

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
    name = re.sub(r"[^a-zA-Z]", "", name)
    email = re.sub(r"[^a-zA-Z]", "", email)
    name = name.replace(" ", "")
    email = email.replace(" ", "")
    num = str(random.randint(0, 999))
    uname = name[3] + email[:7] + num
    return uname

def generatePassword():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(8))
    return password

def Base64Encode(string):
    message_bytes = string.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_string = base64_bytes.decode('ascii')
    return base64_string

def Base64Decode(string):
    base64_bytes = string.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    return

def md5encode(string):
    md5Password = hashlib.md5(string.encode()).hexdigest()
    return md5Password