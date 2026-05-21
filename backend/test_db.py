import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678", 
        database="nutriescan"
    )
    print(" Conectado a MySQL exitosamente")
    conn.close()
except Exception as e:
    print(f" Error: {e}")