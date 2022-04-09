#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd /usr/share
pwd=$1
#wget https://files.phpmyadmin.net/phpMyAdmin/4.8.5/phpMyAdmin-4.8.5-all-languages.zip
wget https://files.phpmyadmin.net/phpMyAdmin/5.1.3/phpMyAdmin-5.1.3-all-languages.zip
unzip phpMyAdmin-5.1.3-all-languages.zip
mv phpMyAdmin-5.1.3-all-languages phpmyadmin
chown -R www-data:www-data /usr/share/phpmyadmin
chmod -R 755 /usr/share/phpmyadmin
secret=`cat /dev/urandom | head -n 32 | md5sum | head -c 32`;
\cp -a -r /usr/share/phpmyadmin/config.sample.inc.php  /usr/share/phpmyadmin/config.inc.php
sed -i "s#^\$cfg\['blowfish_secret'\].*#\$cfg\['blowfish_secret'\] = '${secret}';#" /usr/share/phpmyadmin/config.inc.php
sed -i "s#^\$cfg\['blowfish_secret'\].*#\$cfg\['blowfish_secret'\] = '${secret}';#" /usr/share/phpmyadmin//libraries/config.default.php
#sed -i "s#^\$i]['host'\].*#\$i]['host'\] = '127.0.0.1';#" /usr/share/phpmyadmin/config.inc.php
#sed -i "s#^\$i]['host'\].*#\$i]['host'\] = '127.0.0.1';#" /usr/share/phpmyadmin//libraries/config.default.php

cat > /etc/nginx/snippets/phpmyadmin.conf <<EOF
location /phpmyadmin {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/phpmyadmin/(.+\.php)$ {
        root /usr/share/;
		include php.conf;
    }
    location ~* ^/phpmyadmin/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF


cd /usr/share
wget https://github.com/roundcube/roundcubemail/releases/download/1.4.13/roundcubemail-1.4.13-complete.tar.gz
tar xvf roundcubemail-1.4.13-complete.tar.gz
mv roundcubemail-1.4.13 roundcube
chown -R www-data:www-data /usr/share/roundcube
mysql -u root -p${pwd} -e "CREATE USER 'roundcube'@'localhost' IDENTIFIED BY '${pwd}';FLUSH PRIVILEGES;"
mysql -u root -p${pwd} -e "create database roundcubedb;FLUSH PRIVILEGES;"
mysql -u root -p${pwd} -e "GRANT ALL PRIVILEGES ON roundcubedb.* TO 'roundcube'@'localhost';FLUSH PRIVILEGES;"
mysql -u root -p${pwd} roundcubedb < /usr/share/roundcube/SQL/mysql.initial.sql
cat > /etc/nginx/snippets/roundcube.conf <<EOF
location /roundcube {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/roundcube/(.+\.php)$ {
        root /usr/share/;
		include php.conf;
    }
    location ~* ^/roundcube/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF
cd /usr/share
wget https://github.com/mayazhanif/web-ftp/raw/main/webftp.zip
unzip webftp.zip
chown -R www-data:www-data /usr/share/webftp
chmod 777 /usr/share/webftp/tmp
cat > /etc/nginx/snippets/webftp.conf <<EOF
location /webftp {
    root /usr/share/;
    index index.php index.html index.htm;
    location ~ ^/webftp/(.+\.php)$ {
        root /usr/share/;
		include php.conf;
    }
    location ~* ^/webftp/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        root /usr/share/;
    }
}
EOF
#echo -e "\n\$cfg['Servers'][\$i]['auth_type'] = 'signon';\n\$cfg['Servers'][\$i]['SignonSession'] = 'SignonSession';\n\$cfg['Servers'][\$i]['SignonURL'] = 'sso.php';\n" >> /usr/share/phpmyadmin/config.inc.php
service nginx restart