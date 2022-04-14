#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
echo "postfix postfix/main_mailer_type string 'Internet Site'" | debconf-set-selections
echo "postfix postfix/mailname string mail.saspanel.org" | debconf-set-selections
echo "dovecot-core dovecot-core/create-ssl-cert boolean true" | debconf-set-selections
mysql -u root -e "CREATE USER 'root'@'localhost' IDENTIFIED BY '${pwd}';FLUSH PRIVILEGES;"
mysql -u root -e "CREATE USER 'admin'@'localhost' IDENTIFIED BY '${pwd}';FLUSH PRIVILEGES;"
mysql -u root -e "GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost';FLUSH PRIVILEGES;"
mysql -u root -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';FLUSH PRIVILEGES;"
mysql -u root -e "create database saspanel;FLUSH PRIVILEGES;"
mysql -u root saspanel < /home/SASPanel/scripts/database.sql
#mysql -u root -e "alter user 'root'@'localhost' identified by '${pwd}';FLUSH PRIVILEGES;"
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${pwd}';;FLUSH PRIVILEGES;"
#mysql -u root -e 'use mysql;update user set plugin="mysql_native_password";FLUSH PRIVILEGES;';
#mysql -hlocalhost -e "FLUSH PRIVILEGES;alter user 'root'@'localhost' identified by '${pwd}';FLUSH PRIVILEGES;";
#echo "Removing skip-grant-tables"
#sed -i '/skip-grant-tables/d' /etc/mysql/mysql.conf.d/mysqld.cnf
echo "Restarting MYSQL"
service mysql restart
echo "The root password set ${pwd}  successuful"