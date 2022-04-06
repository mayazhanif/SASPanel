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
    os.system("chown -R " + name + ":" + name + " /home/" + name + "")
    os.system("chmod 755 /home/" + name + "")
    os.system("setfacl -m user:" + name + ":rx /home/" + name + "")
    print("User Added.")

def add_default_user(username, password):
    print("Adding user: %s" % (username))
    os.system("useradd --create-home \
    --user-group \
    --home /home/" + username + " \
    --shell /bin/rbash \
    --password $(printf %s " + password + " |openssl passwd -1 -stdin) " + username + "")
    os.system("chown " + username + ":" + username + " /home/" + username + "")
    os.system("chmod 755 /home/" + username + "")
    os.system("setfacl -m user:" + username + ":rx /home/" + username + "")
    print("User Added.")
    #os.system("useradd -p `openssl passwd -1 "+password+"` "+username+"")
    os.system('echo "'+username+'" >> /etc/vsftpd.chroot_list')
    os.system("chown -R "+username+":"+username+" /home/"+username+"")
    os.system("chmod 0777 /home/"+username+"")
    #os.system("/bin/bash add_vhost.sh " + username+" "+domain)
#add_usr("testuser3", "testuser3")

def createUser(cursor, userName, password):
    try:
        sqlCreateUser = "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';"%(userName, password)
        cursor.execute(sqlCreateUser)
        print("User Created.")
    except Exception as Ex:
        print("Error creating MySQL User: %s"%(Ex))

def create_database(cursor, DatabaseName,Username):
    try:
        sqlCreateDatabase = "CREATE DATABASE %s;"%(DatabaseName)
        cursor.execute(sqlCreateDatabase)
        print("Database Created.")
        grantPermissions = "GRANT ALL PRIVILEGES ON "+DatabaseName+".* TO '"+Username+"'@'localhost' WITH GRANT OPTION;"
        cursor.execute(grantPermissions)
        print("Permissions Granted on Database.")

    except Exception as Ex:
        print("Error creating MySQL Database: %s"%(Ex))

def changePassword(cursor, username,NewPassword):
    try:
        sqlChangePassword = "alter user '%s'@'localhost' identified by '%s';"%(username, NewPassword)
        cursor.execute(sqlChangePassword)
        print("User Password Changed.")
    except Exception as Ex:
        print("Error Changing MySQL Password: %s"%(Ex))

def drop_database(cursor, DatabaseName):
    try:
        sqlCreateDatabase = "DROP DATABASE %s;"%(DatabaseName)
        cursor.execute(sqlCreateDatabase)
        print("Database Deleted.")

    except Exception as Ex:
        print("Error creating MySQL Database: %s"%(Ex))
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
    #set_mysql_root("DeViL_Master")
    install_packages()
    print("Hello")

def add_vhost(username, domain):
    os.system("/bin/bash scripts/add_vhost.sh " + username+" "+domain)


def add_ftp_only(username, password):
    os.system("useradd -p `openssl passwd -1 "+password+"` "+username+"")
    os.system('echo "'+username+'" >> /etc/vsftpd.chroot_list')
    os.system("chown -R "+username+":"+username+" /home/"+username+"")
    os.system("chmod 0777 /home/"+username+"")
    #os.system("/bin/bash add_vhost.sh " + username+" "+domain)

def add_ftp(ftpusername,username, password):
    os.system("useradd -p `openssl passwd -1 "+password+"` "+ftpusername+" \
    --home /home/" + username)
    os.system('echo "'+ftpusername+'" >> /etc/vsftpd.chroot_list')
    os.system("chown -R "+ftpusername+":"+ftpusername+" /home/"+username+"")
    os.system("chmod 0777 /home/"+username+"/*")


def set_mysql_root(password):
    os.system("/bin/bash scripts/mysql_admin.sh " + password)

def install():
    install_packages()
    print("Install packages Completed.")

def install_packages():
    os.system("sudo apt-get -y update")
    os.system("sudo apt-get -y upgrade")
    os.system("sudo apt-get -y install mysql-server nginx curl wget acl vsftpd")
    set_mysql_root("Master@786")
    os.system("sudo apt-get -y install php-common php-cli php-fpm")
    #os.system("sudo apt-get -y install pure-ftpd")
    os.system("/bin/bash scripts/installer.sh")
    os.system("sudo apt-get -y install zip php-mbstring php-zip php-gd php-mysql")
    os.system("/bin/bash scripts/phpmyadmin_installer.sh")
    #os.system("/bin/bash nginx_config.sh")
