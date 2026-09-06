import mysql.connector
import configparser
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
# Initialise to None before mysql_connect() runs.
# Any code calling mysqlconnection.reconnect() before
# mysql_connect() completes will get a clear AttributeError
# rather than a confusing 'str has no attribute reconnect'.
mysqlconnection = None
def mysql_connect():
  global mysqlconnection
  currentDirectory = os.path.dirname(os.path.abspath(__file__))
  initfile = os.path.join(currentDirectory, 'config.ini')
  config = configparser.RawConfigParser()
  config.read(initfile)
  # FIX R15-01: bare except left DatabaseDetails undefined if [config] section was missing,
  # causing an unhandled NameError in the next try block. Now return None explicitly on failure.
  try:
    DatabaseDetails = dict(config.items('config'))
  except Exception as e:
    print(f'Config parse error: {e}')
    mysqlconnection = None
    return None
  try:
    mysqlconnection = mysql.connector.connect(
      host=DatabaseDetails['host'],
      user=DatabaseDetails['user'],
      password=DatabaseDetails['password'],
      database=DatabaseDetails['database'],
    )
    print("Connection Successfull.")
  except Exception as e:
    print(e)
    mysqlconnection = None
  return mysqlconnection

mysqlconnection = mysql_connect()