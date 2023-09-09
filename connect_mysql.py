import mysql.connector
from mysql.connector import Error

connection = mysql.connector.connect(host='localhost',
                                         database='users_db',
                                         user='apiuser',
                                         password='123456')

cur = connection.cursor()
