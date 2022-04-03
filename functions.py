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
    os.system("chown "+username+":"+username+" /home/"+username+"")
    os.system("chmod 0777 /home/"+username+"")
    #os.system("/bin/bash add_vhost.sh " + username+" "+domain)
#add_usr("testuser3", "testuser3")

def createUser(cursor, userName, password):
    try:
        sqlCreateUser = "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';"%(userName, password)
        cursor.execute(sqlCreateUser)
    except Exception as Ex:
        print("Error creating MySQL User: %s"%(Ex))

def create_database(cursor, DatabaseName,Username):
    try:
        sqlCreateDatabase = "CREATE DATABASE %s;"%(DatabaseName)
        cursor.execute(sqlCreateDatabase)
        grantPermissions = "GRANT ALL PRIVILEGES ON "+DatabaseName+".* TO '"+Username+"'@'localhost' WITH GRANT OPTION;"
        cursor.execute(grantPermissions)
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
    set_mysql_root("DeViL_Master")
    install_packages()
    print("Hello")

def add_vhost(username, domain):
    os.system("/bin/bash add_vhost.sh " + username+" "+domain)


def add_ftp(username, password):
    #os.system("useradd -p `openssl passwd -1 "+password+"` "+username+"")
    os.system('echo "'+username+'" >> /etc/vsftpd.chroot_list')
    os.system("chown "+username+":"+username+" /home/"+username+"")
    os.system("chmod 0777 /home/"+username+"")
    #os.system("/bin/bash add_vhost.sh " + username+" "+domain)

    
def set_mysql_root_old(password):
    os.system("/bin/bash mysql_root.sh " + password)


def set_mysql_root(password):
    root_mysql = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
service mysqld stop
mysqld_safe --skip-grant-tables&
echo '正在修改密码...';
echo 'The set password...';
sleep 6
m_version=$(cat /www/server/mysql/version.pl|grep -E "(5.1.|5.5.|5.6.)")
if [ "$m_version" != "" ];then
    mysql -uroot -e "insert into mysql.user(Select_priv,Insert_priv,Update_priv,Delete_priv,Create_priv,Drop_priv,Reload_priv,Shutdown_priv,Process_priv,File_priv,Grant_priv,References_priv,Index_priv,Alter_priv,Show_db_priv,Super_priv,Create_tmp_table_priv,Lock_tables_priv,Execute_priv,Repl_slave_priv,Repl_client_priv,Create_view_priv,Show_view_priv,Create_routine_priv,Alter_routine_priv,Create_user_priv,Event_priv,Trigger_priv,Create_tablespace_priv,User,Password,host)values('Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','root',password('${pwd}'),'127.0.0.1')"
    mysql -uroot -e "insert into mysql.user(Select_priv,Insert_priv,Update_priv,Delete_priv,Create_priv,Drop_priv,Reload_priv,Shutdown_priv,Process_priv,File_priv,Grant_priv,References_priv,Index_priv,Alter_priv,Show_db_priv,Super_priv,Create_tmp_table_priv,Lock_tables_priv,Execute_priv,Repl_slave_priv,Repl_client_priv,Create_view_priv,Show_view_priv,Create_routine_priv,Alter_routine_priv,Create_user_priv,Event_priv,Trigger_priv,Create_tablespace_priv,User,Password,host)values('Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','root',password('${pwd}'),'localhost')"
    mysql -uroot -e "UPDATE mysql.user SET password=PASSWORD('${pwd}') WHERE user='root'";
else
    mysql -uroot -e "UPDATE mysql.user SET authentication_string='' WHERE user='root'";
    mysql -uroot -e "FLUSH PRIVILEGES";
    mysql -uroot -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${pwd}';";
fi
mysql -uroot -e "FLUSH PRIVILEGES";
pkill -9 mysqld_safe
pkill -9 mysqld
sleep 2
service mysqld start

echo '==========================================='
echo "root密码成功修改为: ${pwd}"
echo "The root password set ${pwd}  successuful"''';

    WriteFile('mysql_root.sh', root_mysql)
    os.system("/bin/bash mysql_root.sh " + password)
    #os.system("rm -f mysql_root.sh")

def install():
    install_packages()
    print("Hello")

def install_packages():
    os.system("sudo apt-get -y install mysql-server nginx curl wget acl vsftpd")
    #os.system("sudo apt-get -y install pure-ftpd")
    os.system("/bin/bash installer.sh")
    #os.system("/bin/bash nginx_config.sh")
