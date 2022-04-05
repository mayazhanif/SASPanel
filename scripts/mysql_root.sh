#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
#sed -i 's/^#skip-grant-tables.*/skip-grant-tables/g' /etc/mysql/mysql.conf.d/mysqld.cnf
mkdir -p /var/run/mysqld
chown mysql:mysql /var/run/mysqld
echo "Adding skip-grant-tables"
echo "skip-grant-tables" >> /etc/mysql/mysql.conf.d/mysqld.cnf
pkill -9 mysqld_safe
pkill -9 mysqld
pkill -9 mysql
#sed -i '$ a skip-grant-tables' /etc/mysql/mysql.conf.d/mysqld.cnf
echo "Stopping MYSQL"
service mysql stop
echo "Starting MYSQL"
service mysql start
echo "Changing Password"
#mysql -e "FLUSH PRIVILEGES;alter user 'root'@'localhost' identified by '${pwd}';FLUSH PRIVILEGES;";
mysql -e 'use mysql;update user set plugin="mysql_native_password";';
mysql -hlocalhost -e "FLUSH PRIVILEGES;alter user 'root'@'localhost' identified by '${pwd}';FLUSH PRIVILEGES;";
echo "Removing skip-grant-tables"
sed -i '/skip-grant-tables/d' /etc/mysql/mysql.conf.d/mysqld.cnf
echo "Restarting MYSQL"
service mysql restart
echo "The root password set ${pwd}  successuful"