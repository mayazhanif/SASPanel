import base64
import hashlib
import re
import os

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
    print("Done.")


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


def set_mysql_root(password):
    # import db,os
    # sql = db.Sql()

    root_mysql = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
/etc/init.d/mysqld stop
mysqld_safe --skip-grant-tables&
echo 'Changing password...';
sleep 6
m_version=$(cat /www/server/mysql/version.pl|grep -E "(5.1.|5.5.|5.6.|10.0|10.1)")
m2_version=$(cat /www/server/mysql/version.pl|grep -E "(10.5.|10.4.)")
if [ "$m_version" != "" ];then
    mysql -uroot -e "UPDATE mysql.user SET password=PASSWORD('${pwd}') WHERE user='root'";
elif [ "$m2_version" != "" ];then
    mysql -uroot -e "FLUSH PRIVILEGES;alter user 'root'@'localhost' identified by '${pwd}';alter user 'root'@'127.0.0.1' identified by '${pwd}';FLUSH PRIVILEGES;";
else
    m_version=$(cat /www/server/mysql/version.pl|grep -E "(5.7.|8.0.)")
    if [ "$m_version" != "" ];then
        mysql -uroot -e "FLUSH PRIVILEGES;update mysql.user set authentication_string='' where user='root' and (host='127.0.0.1' or host='localhost');alter user 'root'@'localhost' identified by '${pwd}';alter user 'root'@'127.0.0.1' identified by '${pwd}';FLUSH PRIVILEGES;";
    else
        mysql -uroot -e "update mysql.user set authentication_string=password('${pwd}') where user='root';"
    fi
fi
mysql -uroot -e "FLUSH PRIVILEGES";
pkill -9 mysqld_safe
pkill -9 mysqld
pkill -9 mysql
sleep 2
/etc/init.d/mysqld start

echo '==========================================='
echo "The root password set ${pwd}  successuful"''';

    WriteFile('mysql_root.sh', root_mysql)
    os.system("/bin/bash mysql_root.sh " + password)
    # os.system("rm -f mysql_root.sh")

    # result = sql.table('config').where('id=?',(1,)).setField('mysql_root',password)
    #print("Hello")


#set_mysql_root("Master@786")