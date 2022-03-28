import mysql.connector
import configparser
import os

currentDirectory = os.path.dirname(os.path.abspath(__file__))
initfile = os.path.join(currentDirectory, 'DB.txt')


config = configparser.RawConfigParser()
config.read(initfile)
DatabaseDetails = dict(config.items('configlocal'))
mysqlconnection = None
try:
  #print(DatabaseDetails['password'])
  mysqlconnection = mysql.connector.connect(
    host=DatabaseDetails['host'],
    user=DatabaseDetails['user'],
    password=DatabaseDetails['password'],
    database=DatabaseDetails['database']
  )
  #print(mysqlconnection)
  #host = "localhost",
  #user = "root",
  #password = "",
  #database = "saspanel"
except:
  mysqlconnection = None