import mysql.connector
import configparser
import os
localconfig=True
currentDirectory = os.path.dirname(os.path.abspath(__file__))
initfile = os.path.join(currentDirectory, 'DB.txt')


config = configparser.RawConfigParser()
config.read(initfile)
if localconfig==True:
  DatabaseDetails = dict(config.items('configlocal'))
else:
  DatabaseDetails = dict(config.items('config'))

mysqlconnection = None
try:
  #print(DatabaseDetails['password'])
  mysqlconnection = mysql.connector.connect(
    host=DatabaseDetails['host'],
    user=DatabaseDetails['user'],
    password=DatabaseDetails['password'],
    database=DatabaseDetails['database']
  )
except:
  mysqlconnection = None