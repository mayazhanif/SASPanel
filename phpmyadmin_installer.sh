#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd /usr/share
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