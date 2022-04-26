import mysql.connector
import configparser
import os
import os
from flask import current_app as app

def WriteConfig(password):
  currentDirectory = os.path.dirname(os.path.abspath(__file__))
  initfile = os.path.join(currentDirectory, 'config.ini')
  config = configparser.RawConfigParser()
  config.read(initfile)
  DatabaseDetails = config["config"]
  DatabaseDetails["password"] = password
  with open(initfile, 'w') as conf:
    config.write(conf)

def WriteMailConfig(email,password):
  currentDirectory = os.path.dirname(os.path.abspath(__file__))
  initfile = os.path.join(currentDirectory, 'config.ini')
  config = configparser.RawConfigParser()
  config.read(initfile)
  DatabaseDetails = config["mail"]
  DatabaseDetails["email"] = email
  DatabaseDetails["password"] = password
  with open(initfile, 'w') as conf:
    config.write(conf)

localconfig=False
currentDirectory = os.path.dirname(os.path.abspath(__file__))
initfile = os.path.join(currentDirectory, 'config.ini')
config = configparser.RawConfigParser()
config.read(initfile)
if localconfig==True:
  DatabaseDetails = dict(config.items('configlocal'))
else:
  DatabaseDetails = dict(config.items('config'))

mysqlconnection = None
try:
  mysqlconnection = mysql.connector.connect(
    host=DatabaseDetails['host'],
    user=DatabaseDetails['user'],
    password=DatabaseDetails['password'],
    database=DatabaseDetails['database']
  )
except:
  mysqlconnection = None

mailDetails = dict(config.items('mail'))
app.config['MAIL_SERVER'] = mailDetails['server']
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = mailDetails['email']
app.config['MAIL_PASSWORD'] = mailDetails['password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False

