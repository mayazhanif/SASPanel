crontab -e  # opening cron editor
* 1 1 * * cronfunc
cronfunc(){
    echo "Hello"
}