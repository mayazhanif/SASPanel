#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
username=$1
croncommand=$2
echo "$username" >> /etc/cron.allow
touch /var/spool/cron/$username
/usr/bin/crontab /var/spool/cron/$username
CRON_FILE="/var/spool/cron/$username"
if [ ! -f $CRON_FILE ]; then
   echo "cron file for root doesnot exist, creating.."
   touch $CRON_FILE
   /usr/bin/crontab $CRON_FILE
fi
grep -qi "cleanup_script" $CRON_FILE
if [ $? != 0 ]; then
   echo "Updating cron job for cleaning temporary files"
       /bin/echo "* * * * * php index.php >> /home/$username/crobjobs/logs/logg.cron" >> $CRON_FILE
fi
mkdir -m 777 -p /home/$username/crobjobs/logs
chown -R www-data:www-data /home/$username/crobjobs/logs/*
chown -R $username:$username /home/$username/crobjobs/logs/*