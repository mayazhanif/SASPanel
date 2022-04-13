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
cp /usr/share/roundcube/config/config.inc.php.sample /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['db_dsnw'\] =\).*$|\1 \'mysqli://roundcube:${pwd}@localhost/roundcubedb\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_server'\] =\).*$|\1 \'localhost\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_user'\] =\).*$|\1 \'%u\';|" /usr/share/roundcube/config/config.inc.php
sed -i "s|^\(\$config\['smtp_pass'\] =\).*$|\1 \'%p\';|" /usr/share/roundcube/config/config.inc.php
#sed -i "s|^\(\$config\['support_url'\] =\).*$|\1 \'mailto:${E}\';|" /var/www/html/roundcube/config/config.inc.php
deskey=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9-_#&!*%?' | fold -w 24 | head -n 1)
sed -i "s|^\(\$config\['des_key'\] =\).*$|\1 \'${deskey}\';|" /usr/share/roundcube/config/config.inc.php
rm -rf /usr/share/roundcube/installer