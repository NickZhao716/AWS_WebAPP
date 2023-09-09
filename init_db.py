import mysql.connector
import sys


def initializeDB():
    db = mysql.connector.connect(host=sys.argv[1], user="csye6225", password="Maxim123456")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE users_db")
    # cursor.execute("SHOW DATABASES")
    cursor.execute("CREATE USER 'apiuser'@'%' IDENTIFIED BY '123456'")
    cursor.execute("GRANT ALL PRIVILEGES ON users_db.*  TO 'apiuser'@'%'")


initializeDB()
