"""
Gestión de cuota diaria de escaneos usando MySQL.
Cuota compartida entre /vision y /recetas.
"""

from datetime import date
from config.database import get_connection
from mysql.connector import Error


class CuotaDiariaService:
    
    LIMITE_DIARIO = 15  # Configurable
    
    @staticmethod
    def obtener_escaneos_hoy(user_id: int) -> int:
        """
        Devuelve cuántos escaneos ha hecho el usuario HOY.
        """
        hoy = date.today()
        connection = None
        
        try:
            connection = get_connection()
            if connection is None:
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT escaneos_realizados 
                FROM cuota_diaria 
                WHERE user_id = %s AND fecha = %s
            """
            cursor.execute(query, (user_id, hoy))
            result = cursor.fetchone()
            
            if result:
                return result['escaneos_realizados']
            return 0
            
        except Error as e:
            print(f"Error consultando escaneos: {e}")
            return 0
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    @staticmethod
    def puede_escanear(user_id: int):
        """
        Verifica si el usuario puede hacer un escaneo más HOY.
        
        Returns:
            tuple: (puede_escanear, escaneos_actuales, limite_diario)
        """
        actuales = CuotaDiariaService.obtener_escaneos_hoy(user_id)
        puede = actuales < CuotaDiariaService.LIMITE_DIARIO
        return puede, actuales, CuotaDiariaService.LIMITE_DIARIO
    
    @staticmethod
    def incrementar_escaneo(user_id: int) -> int:
        """
        Incrementa el contador de escaneos para el usuario HOY.
        Si es el primer escaneo del día, crea el registro.
        
        Returns:
            int: Nuevo total de escaneos del día
        """
        hoy = date.today()
        connection = None
        
        try:
            connection = get_connection()
            if connection is None:
                print("Error: No se pudo conectar a la base de datos")
                return CuotaDiariaService.LIMITE_DIARIO
                
            cursor = connection.cursor()
            
            # Intentar insertar (si es primer escaneo del día)
            query_insert = """
                INSERT INTO cuota_diaria (user_id, fecha, escaneos_realizados)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE escaneos_realizados = escaneos_realizados + 1
            """
            cursor.execute(query_insert, (user_id, hoy))
            connection.commit()
            
            # Obtener el valor actualizado
            query_select = """
                SELECT escaneos_realizados 
                FROM cuota_diaria 
                WHERE user_id = %s AND fecha = %s
            """
            cursor.execute(query_select, (user_id, hoy))
            result = cursor.fetchone()
            
            return result[0] if result else 1
            
        except Error as e:
            print(f"Error incrementando escaneo: {e}")
            # Si falla, asumimos que ya llegó al límite (seguridad)
            return CuotaDiariaService.LIMITE_DIARIO
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    @staticmethod
    def resetear_cuota(user_id: int) -> None:
        """Resetea la cuota de HOY (solo para pruebas/admin)."""
        hoy = date.today()
        connection = None
        
        try:
            connection = get_connection()
            if connection is None:
                print("Error: No se pudo conectar a la base de datos")
                return
                
            cursor = connection.cursor()
            query = "DELETE FROM cuota_diaria WHERE user_id = %s AND fecha = %s"
            cursor.execute(query, (user_id, hoy))
            connection.commit()
            print(f"Cuota reseteada para user_id={user_id}")
            
        except Error as e:
            print(f"Error reseteando cuota: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()