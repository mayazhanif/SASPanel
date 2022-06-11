import base64
import hashlib
import re
import os
from this import d
from flask import session, render_template
import random
import string
from Database.DbConfig import mysqlconnection, WriteConfig, WriteMailConfig
from flask_mail import Mail, Message
from flask import current_app as app
from cachelib import SimpleCache
import psutil
import sys
import time
from hashlib import md5
cache = SimpleCache()

def get_error_info():
    import traceback
    errorMsg = traceback.format_exc()
    return errorMsg

def get_preexec_fn(run_user):
    import pwd
    pid = pwd.getpwnam(run_user)
    uid = pid.pw_uid
    gid = pid.pw_gid

    def _exec_rn():
        os.setgid(gid)
        os.setuid(uid)
    return _exec_rn

def ExecShell(cmdstring, timeout=None, shell=True,cwd=None,env=None,user = None):
    a = ''
    e = ''
    import subprocess,tempfile
    preexec_fn = None
    tmp_dir = '/dev/shm'
    if user:
        preexec_fn = get_preexec_fn(user)
        tmp_dir = '/tmp'
    try:
        rx = md5(cmdstring)
        succ_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_succ',prefix='btex_' + rx ,dir=tmp_dir)
        err_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_err',prefix='btex_' + rx ,dir=tmp_dir)
        sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell,bufsize=128,stdout=succ_f,stderr=err_f,cwd=cwd,env=env,preexec_fn=preexec_fn)
        if timeout:
            s = 0
            d = 0.01
            while sub.poll() is None:
                time.sleep(d)
                s += d
                if s >= timeout:
                    if not err_f.closed: err_f.close()
                    if not succ_f.closed: succ_f.close()
                    return 'Timed out'
        else:
            sub.wait()

        err_f.seek(0)
        succ_f.seek(0)
        a = succ_f.read()
        e = err_f.read()
        if not err_f.closed: err_f.close()
        if not succ_f.closed: succ_f.close()
    except:
        return '',get_error_info()
    try:
        #编码修正
        if type(a) == bytes: a = a.decode('utf-8')
        if type(e) == bytes: e = e.decode('utf-8')
    except:pass

    return a,e

def getCpuType():
    cpuinfo = open('/proc/cpuinfo', 'r').read()
    rep = "model\s+name\s+:\s+(.+)"
    tmp = re.search(rep, cpuinfo, re.I)
    cpuType = ''
    if tmp:
        cpuType = tmp.groups()[0]
    else:
        cpuinfo = ExecShell('LANG="en_US.UTF-8" && lscpu')[0]
        rep = "Model\s+name:\s+(.+)"
        tmp = re.search(rep, cpuinfo, re.I)
        if tmp: cpuType = tmp.groups()[0]
    return cpuType


def GetCpuInfo(interval=1):
    cpuCount = psutil.cpu_count()
    cpuNum = psutil.cpu_count(logical=False)
    c_tmp = readFile('/proc/cpuinfo')
    d_tmp = re.findall("physical id.+", c_tmp)
    cpuW = len(set(d_tmp))
    import threading
    p = threading.Thread(target=get_cpu_percent_thead, args=(interval,))
    p.setDaemon(True)
    p.start()

    used = cache.get('cpu_used_all')
    if not used: used = get_cpu_percent_thead(interval)

    used_all = psutil.cpu_percent(percpu=True)
    cpu_name = getCpuType() + " * {}".format(cpuW)

    return used, cpuCount, used_all, cpu_name, cpuNum, cpuW


def get_cpu_percent_thead(interval=1):
    used = psutil.cpu_percent(interval)
    cache.set('cpu_used_all', used, 10)
    return used


def ReadFile(filename, mode='r'):
    import os
    if not os.path.exists(filename): return False
    try:
        fp = open(filename, mode)
        f_body = fp.read()
        fp.close()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode, encoding="utf-8")
                f_body = fp.read()
                fp.close()
            except:
                fp = open(filename, mode, encoding="GBK")
                f_body = fp.read()
                fp.close()
        else:
            return False
    return f_body


def readFile(filename, mode='r'):
    return ReadFile(filename, mode)


def GetLoadAverage():
    try:
        c = os.getloadavg()
        #print(c)
    except Exception as e:  # work on python 3.x
        print('Error CPU ' + str(e))
        c = [0, 0, 0]
    data = {}
    data['one'] = float(c[0])
    data['five'] = float(c[1])
    data['fifteen'] = float(c[2])
    data['max'] = psutil.cpu_count() * 2
    data['limit'] = data['max']
    data['safe'] = data['max'] * 0.75
    return data


def GetMemInfo(get=None):
    skey = 'memInfo'
    memInfo = cache.get(skey)
    if memInfo: return memInfo
    mem = psutil.virtual_memory()
    memInfo = {'memTotal': int(mem.total / 1024 / 1024), 'memFree': int(mem.free / 1024 / 1024),
               'memBuffers': int(mem.buffers / 1024 / 1024), 'memCached': int(mem.cached / 1024 / 1024)}
    memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
    cache.set(skey, memInfo, 60)
    return memInfo


def GetSystemVersion():
    key = 'sys_version'
    version = cache.get(key)
    if version: return version
    version = readFile('/etc/redhat-release')
    if not version:
        version = readFile('/etc/issue').strip().split("\n")[0].replace('\\n', '').replace('\l', '').strip()
    else:
        version = version.replace('release ', '').replace('Linux', '').replace('(Core)', '').strip()
    v_info = sys.version_info
    version = version + '(Py' + str(v_info.major) + '.' + str(v_info.minor) + '.' + str(v_info.micro) + ')'
    cache.set(key, version, 600)
    return version


def GetBootTime():
    key = 'sys_time'
    sys_time = cache.get(key)
    if sys_time: return sys_time
    import math
    conf = readFile('/proc/uptime').split()
    tStr = float(conf[0])
    min = tStr / 60
    hours = min / 60
    days = math.floor(hours / 24)
    hours = math.floor(hours - (days * 24))
    min = math.floor(min - (days * 60 * 24) - (hours * 60))
    sys_time = "{} Day(s)".format(int(days))
    cache.set(key, sys_time, 1800)
    return sys_time


def get_cpu_times():
    skey = 'cpu_times'
    data = cache.get(skey)
    if data: return data
    try:
        data = {}
        cpu_times_p = psutil.cpu_times_percent()
        data['user'] = cpu_times_p.user
        data['nice'] = cpu_times_p.nice
        data['system'] = cpu_times_p.system
        data['idle'] = cpu_times_p.idle
        data['iowait'] = cpu_times_p.iowait
        data['irq'] = cpu_times_p.irq
        data['softirq'] = cpu_times_p.softirq
        data['steal'] = cpu_times_p.steal
        data['guest'] = cpu_times_p.guest
        data['guest_nice'] = cpu_times_p.guest_nice
        data['total_processes'] = 0
        data['active_processes'] = 0
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if p.status() == 'running':
                    data['active_processes'] += 1
            except:
                continue
            data['total_processes'] += 1

        cache.set(skey, data, 60)
    except:
        return None
    return data


def get_process_cpu_time():
    pids = psutil.pids()
    cpu_time = 0.00
    for pid in pids:
        try:
            cpu_times = psutil.Process(pid).cpu_times()
            for s in cpu_times: cpu_time += s
        except:
            continue
    return cpu_time


def get_cpu_time():
    cpu_time = 0.00
    cpu_times = psutil.cpu_times()
    for s in cpu_times: cpu_time += s
    return cpu_time


def get_cpu_percent():
    percent = 0.00
    old_cpu_time = cache.get('old_cpu_time')
    old_process_time = cache.get('old_process_time')
    if not old_cpu_time:
        old_cpu_time = get_cpu_time()
        old_process_time = get_process_cpu_time()
        time.sleep(1)
    new_cpu_time = get_cpu_time()
    new_process_time = get_process_cpu_time()
    try:
        percent = round(100.00 * ((new_process_time - old_process_time) / (new_cpu_time - old_cpu_time)), 2)
    except:
        percent = 0.00
    cache.set('old_cpu_time', new_cpu_time)
    cache.set('old_process_time', new_process_time)
    if percent > 100: percent = 100
    if percent > 0: return percent
    return 0.00


def GetAllInfo():
    data = {}
    data['load_average'] = GetLoadAverage()
    # data['title'] = GetTitle()
    # data['network'] = GetNetWorkApi(get)
    data['cpu'] = GetCpuInfo(1)
    data['time'] = GetBootTime()
    data['system'] = GetSystemVersion()
    data['mem'] = GetMemInfo()
    data['cpu_percentage'] = get_cpu_percent()
    # data['version'] = session['version']
    return data





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
        return False

def check_admin_Login():
    if check_Session("Admin"):
        return True
    else:
        return False

def generateservUser(name, email):
    name = re.sub(r"[^a-zA-Z]", "", name)
    email = re.sub(r"[^a-zA-Z]", "", email)
    name = name.replace(" ", "")
    email = email.replace(" ", "")
    num = str(random.randint(0, 999))
    uname = name + email[:3] + num
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

def mailSender(title,receipt,body,type="PLAIN"):
    mail = Mail(app)
    msg = Message(title, sender='support@saspanel.com', recipients=[receipt])
    if type=="PLAIN":
        msg.body = body
    else:
        msg.html = body
    mail.send(msg)
    return "Sent"

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
    os.system('echo "'+username+'" >> /etc/vsftpd.chroot_list')
    os.system("chown -R "+username+":"+username+" /home/"+username+"")
    os.system("chmod 0777 /home/"+username+"")
    #os.system("/bin/bash add_vhost.sh " + username+" "+domain)

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

def create_mail_user(cursor, email,password):
    try:
        cursor.execute("USE mail")
        cursor.execute("INSERT INTO `users` (`email`, `password`) VALUES ('"+email+"', '"+password+"');")
        mysqlconnection.commit()
        print("Mail Account Added.")
        cursor.execute("USE saspanel;")
    except Exception as Ex:
        cursor.execute("USE saspanel;")
        print("Error Adding Record: %s"%(Ex))

def add_mail_domain(cursor, domain):
    try:
        cursor.execute("USE mail")
        cursor.execute("INSERT INTO `domains` (`domain`) VALUES ('"+domain+"');")
        mysqlconnection.commit()
        print("Mail Account Added.")
        cursor.execute("USE saspanel;")
    except Exception as Ex:
        cursor.execute("USE saspanel;")
        print("Error Adding Record: %s"%(Ex))

def change_mail_password(cursor, Email,Password):
    try:
        cursor.execute("USE mail")
        #cursor.execute("INSERT INTO `domains` (`domain`) VALUES ('"+domain+"');")
        cursor.execute("UPDATE `users` SET `password` = '"+Password+"' WHERE email = '"+Email+"';")
        mysqlconnection.commit()
        print("Mail Password Changed.")
        cursor.execute("USE saspanel;")
    except Exception as Ex:
        cursor.execute("USE saspanel;")
        print("Error Changing Password: %s"%(Ex))


def validateEmail(email):
   regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
   if (re.fullmatch(regex, email)):
       return True
   return False

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

def remove_vhost(domain):
    os.system("rm /etc/nginx/sites-enabled/"+domain+"-vhost.conf")
    os.system("systemctl restart nginx")
    #os.system("mv /etc/nginx/sites-available/"+domain+"-vhost.conf /etc/nginx/backupDomains/")

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

def remove_ftp(ftpusername):
    os.system("chage -E0 "+ftpusername)
    os.system('usermod -s /sbin/nologin '+ftpusername)

def change_ftp_pass(ftpUsername,ftpPassword):
    os.system("echo '"+ftpUsername+":"+ftpPassword+"' | sudo chpasswd")

def set_mysql_root(password):
    os.system("/bin/bash scripts/mysql_admin.sh " + password)


def readLines(fname, N):
    data=""
    try:
        with open(fname) as file:
            lines = file.readlines()
            last_lines = lines[-N:]
            data = listToString(last_lines)
        file.close()
        return data
    except:
        return "File Does not Exists."

def listToString(s):
    returnData = ""
    return (returnData.join(s))

def addCronJobOld(username,croncommand,logfile):
    os.system("mkdir -m 777 -p /home/"+username+"/crobjobs/logs")
    #os.system("chown -R www-data:www-data /home/"+username+"/crobjobs/logs/*")
    os.system("chown -R "+username+":"+username+" /home/"+username+"/crobjobs/logs/*")
    comand='echo "'+croncommand+'" >> mycron'
    os.system(comand)
    os.system("crontab -u "+username+" mycron")
    os.system("rm mycron")
    print(comand)
    return True

def addCronJob(username,croncommand,logfile):
    os.system("/bin/bash scripts/add_cron_job.sh " + username+" "+croncommand)

def deleteCronJob(username):
    comand='echo "" >> mycron'
    os.system(comand)
    os.system("crontab -u "+username+" mycron")
    os.system("rm mycron")

def generate_SSL(domain,email):
    os.system("/bin/bash scripts/ssl_certificate_generate.sh " + domain+" "+email)
def renewALLSSL():
    os.system("certbot renew --force-renewal")

def install():
    install_packages()
    print("Install packages Completed.")

def install_packages(root_password, mail_password,domain,emailaddress,emailpassword):
    os.system("sudo apt-get -y update")
    os.system("sudo apt-get -y upgrade")
    os.system("mv /home/SASPanel/scripts/sample.config.ini /home/SASPanel/Database/config.ini")
    WriteConfig(root_password)
    WriteMailConfig(emailaddress,emailpassword)
    os.system("sudo apt-get -y install mysql-server nginx curl wget acl vsftpd")
    os.system("sudo apt-get -y install certbot python3-certbot-nginx")
    set_mysql_root(root_password)
    os.system("sudo apt-get -y install php-common php-cli php-fpm")
    os.system("sudo apt-get install dovecot-core dovecot-imapd dovecot-pop3d dovecot-lmtpd dovecot-mysql -y > /dev/null 2>&1")
    os.system("sudo apt-get -y install postfix-mysql")
    os.system("/bin/bash scripts/installer.sh")
    os.system("sudo apt install -y php-mysql php-net-ldap2 php-net-ldap3 php-imagick php-common php-gd php-imap php-json php-curl php-zip php-xml php-mbstring php-bz2 php-intl php-gmp php-net-smtp php-mail-mime php-net-idna2 mailutils")
    os.system("sudo apt-get -y install zip php-mbstring php-zip php-gd php-mysql")
    os.system("/bin/bash scripts/packages_installer.sh "+root_password+" "+mail_password+" "+domain+" "+emailaddress+" "+emailpassword+" ")
    os.system("cp /home/SASPanel/scripts/saspanel.service /etc/systemd/system")
    print("Package Installer Done")
    os.system("systemctl daemon-reload")
    print("Daemon Reload Done")
    os.system("systemctl enable saspanel")
    os.system("systemctl enable dovecot")
    os.system("systemctl enable postfix")
    os.system("systemctl start postfix")
    os.system("systemctl start dovecot")
    print("Daemon Reload Done")
    os.system("systemctl restart saspanel")
    print("SASPanel Restart Done")
    print("Install packages Completed.")