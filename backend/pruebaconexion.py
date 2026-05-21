# ES PARA HACER LA PRUEBA DE QUE ESTA CONECTADO CON RAILWAY


import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    port=os.getenv("MYSQLPORT"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE")
)

cursor = conn.cursor()

print("MYSQL CONECTADO")