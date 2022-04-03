#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
#sudo service mysql stop
sudo mkdir /var/run/mysqld
sudo chown mysql: /var/run/mysqld
mysqld_safe --skip-grant-tables&
echo 'Changing password...';
sleep 6
#mysql -uroot -e "FLUSH PRIVILEGES;'ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY ''${pwd}'';FLUSH PRIVILEGES;";
mysql -uroot -e "FLUSH PRIVILEGES;alter user 'root'@'localhost' identified by '${pwd}';FLUSH PRIVILEGES;";
mysql -uroot -e "FLUSH PRIVILEGES";
pkill -9 mysqld_safe
pkill -9 mysqld
pkill -9 mysql
sleep 2
sudo service mysql start

echo '==========================================='
echo "The root password set ${pwd}  successuful"