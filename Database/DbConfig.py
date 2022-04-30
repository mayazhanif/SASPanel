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

# currentDirectory = os.path.dirname(os.path.abspath(__file__))
# initfile = os.path.join(currentDirectory, 'config.ini')
# config = configparser.RawConfigParser()
# config.read(initfile)
# DatabaseDetails = dict(config.items('config'))
# mysqlconnection = None
# try:
#   mysqlconnection = mysql.connector.connect(
#     host=DatabaseDetails['host'],
#     user=DatabaseDetails['user'],
#     password=DatabaseDetails['password'],
#     database=DatabaseDetails['database']
#   )
# except:
#   mysqlconnection = None

def mysql_connect():
  currentDirectory = os.path.dirname(os.path.abspath(__file__))
  initfile = os.path.join(currentDirectory, 'config.ini')
  config = configparser.RawConfigParser()
  config.read(initfile)
  try:
    DatabaseDetails = dict(config.items('config'))
  except:
    mysqlconnection = None
  mysqlconnection = None
  try:
    mysqlconnection = mysql.connector.connect(
      host=DatabaseDetails['host'],
      user=DatabaseDetails['user'],
      password=DatabaseDetails['password'],
      database=DatabaseDetails['database'],
    )
    #mysqlconnection= "testValue"
    print("Connection Successfull.")
  except Exception as e:
    print(e.message)
    mysqlconnection = None
  return mysqlconnection

mysqlconnection = mysql_connect()