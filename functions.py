import base64
import hashlib
import re
import os
from this import d

from flask import session, render_template
import random
import string
from Database.DbConfig import mysqlconnection


def WriteFile(filename,s_body,mode='w+'):
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False

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


# add user function
def add_usr(name, password):
    #name = username
    print("Adding user: %s" % (name))
    os.system("useradd --create-home \
    --user-group \
    --home /home/" + name + " \
    --shell /bin/rbash \
    --password $(printf %s " + password + " |openssl passwd -1 -stdin) " + name + "")
    os.system("chown " + name + ":" + name + " /home/" + name + "")
    os.system("chmod 755 /home/" + name + "")
    os.system("setfacl -m user:" + name + ":rx /home/" + name + "")
    print("User Added.")


#add_usr("testuser3", "testuser3")

def createUser(cursor, userName, password):
    try:
        sqlCreateUser = "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';"%(userName, password)
        cursor.execute(sqlCreateUser)
    except Exception as Ex:
        print("Error creating MySQL User: %s"%(Ex))


def WriteFile(filename, s_body, mode='w+'):
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode, encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False
def install():
    install_packages()
    print("Hello")

def add_vhost(username, domain):
    os.system("/bin/bash add_vhost.sh " + username+" "+domain)

    
def set_mysql_root(password):
    os.system("/bin/bash mysql_root.sh " + password)
def install():
    install_packages()
    print("Hello")

def install_packages():
    os.system("/bin/bash installer.sh")
    os.system("/bin/bash nginx_config.sh")
