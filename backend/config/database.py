import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# BUSCA Y GUARDA EN MEMORIAS LAS VARIABLES DE ENTORNO PARA 
# DESPUES USARLAR
load_dotenv()

# OBTENEMOS UNA CONEXION ALA BASE DE DATOS
def get_connection(): 
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "nutriescan"),
            port=os.getenv("DB_PORT", 3306)
        )
        
        return connection
    
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
        return None