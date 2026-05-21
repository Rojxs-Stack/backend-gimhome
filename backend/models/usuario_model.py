# ACA VAN TODAS LAS CONSULTAS SQL PROFESIONALES



from config.database import get_connection
from mysql.connector import Error

#preguntas
# no debrian ser las funciones mejor asincronas?


# MODELO PARA MANEJAR AL USUARIO EN LA DB
class UsuarioModel:
    
    # le decimos que este metodo sera un metodo estatico
    # sera un metodo de la clase, este no se necesita instanciar
    # se accede solo desde la clase asi es mas comodo y no necesitamos
    # instanciar objetos para llamarla.
    
    # le decimos que los valores por defecto son None pero
    # que si llega un valor que lo sobreescriba
    
    @staticmethod
    def guardar_y_descontar_macros(user_id,nombre, calorias, proteinas, grasas, carbohidratos, azucares):
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO historialconsumidopordia (usuario_id,nombre, calorias, proteinas, grasas, carbohidratos, azucares) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            cursor.execute(query, (user_id, nombre, calorias, proteinas, grasas, carbohidratos, azucares))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    
    # CREAR UN USUARIO NUEVO DESDE GOOGLE
    @staticmethod 
    def create_from_google(email, nombre= None, google_id=None, foto_url= None):
        
        
        connection = get_connection() 
        cursor = None # el que lleva y trae respuestas como stmt en php
        
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO usuario (email,nombre,google_id,foto_url,activo) VALUES (%s, %s, %s, %s, 1)
            """
            #ejecutamos la consulta y le pasamos los parametros como
            #una tupla
            cursor.execute(query,(email, nombre, google_id, foto_url))
            
            #guardamos los cambios
            connection.commit()
            
            
            
            
            return {
                "success" : "True",
                # devuelve el id numerico de la base de datos
                # que le acabo de asignar a este usuario en especifico
                "user_id" : cursor.lastrowid,
                "email" : email
            }
        
        
        
        
        except Error as e:
            print(f"Error: {e}")
            return {"success": False, "error": str(e)}
        
        
        finally:
            if cursor:
                cursor.close()
                
            if connection:
                connection.close()
                
    @staticmethod
    def get_by_id(user_id: int):
        """Obtiene usuario por ID"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM usuario WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            print("get_by_id result:", result)  # 👈 Agregá este print para debug
            return result
        except Exception as e:
            print(f"Error en get_by_id: {e}")
            return None
        finally:
            cursor.close()
            conn.close()           
                
                
                
                
                
      
    # BUSCA UN USUARIO POR EMAIL          
    @staticmethod
    def get_by_email(email):
        connection = get_connection()
        cursor = None
         
        try:
            
            #cursor por defecto manda filas de tuplas con los datos
            #aqui le decimos que mande un diccionario donde la clave
            #sera el nombre de la columna y los datos seran los datos
            cursor = connection.cursor(dictionary = True)
            
            
            query = "SELECT * FROM usuario WHERE email = %s"
            
            cursor.execute(query, (email,))
            
            #le decimos que solo devuelva la primera fila que encontro en la DB
            # asi nos aseguramos que solo devuelva un usuario
            # el usuario que buscamos
            user = cursor.fetchone()
            
            #le decimos que si user es True (tiene algo dentro)
            #retorne user en caso contrario retorne None
            return user if user else None
        
        except Error as e:
            print(f"Error: {e}")
            return None
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            
            
    # ACTUALIZA USUARIO CON DATOS DE GOOGLE
    @staticmethod
    def update_google_data(user_id, nombre, google_id, foto_url):
          
        connection = get_connection()
          
        cursor = None
     
        try:
              
            #cursor es un metodo que devuelve la conexion ala DB
            #que crea ese objeto que lleva y trae las respuestas
            cursor = connection.cursor()


            query = """
            UPDATE usuario SET nombre = %s, google_id = %s, foto_url = %s, activo = 1 WHERE id = %s
            """


            cursor.execute(query, (nombre, google_id,foto_url, user_id))
            connection.commit()


            return {"succes" : True}
          
          
        except Error as e:
            print(f"Error {e}")
            return {"success" : False, "error": str(e)}
        
        
        finally:
            if cursor:
                cursor.close()
                
            if connection:
                connection.close()
                
                
                
                
            
    @staticmethod
    def updateDateCorporal(user_id: int, data: dict):
        
        if not data:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        #CONSTRUIR SET DINAMICO
        campos = []
        valores = []
        
        for key,value in data.items():
            campos.append(f"{key} = %s")
            valores.append(value)
            
        #ultimo valor para el where
        valores.append(user_id)
        query = f"UPDATE datoscorporales SET {', '.join(campos)} WHERE usuario_id = %s"
            
        try:
            cursor.execute(query, valores)
            conn.commit()
            return cursor.rowcount > 0
        
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            return False
        
        finally:
            cursor.close()
            conn.close()
            
            
            
            
            
            
            
    @staticmethod
    def update(user_id: int, data: dict):
        
        # actualiza campos especificos de un usuario
        
        if not data:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
         #Construir el SET dinamico
        campos = []
        valores = []
        
        for key,value in data.items():
            campos.append(f"{key} = %s")  
            valores.append(value)      
            
        valores.append(user_id)
        query = f"UPDATE usuario SET {', '.join(campos)} WHERE id = %s"
        
        try: 
            cursor.execute(query, valores)
            conn.commit()
            return cursor.rowcount > 0
        
        except Exception as e:
            print(f"Error actualizando usuario: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
            
            
            
    @staticmethod
    def savedDateCorporal(user_id: int , altura: float, peso: float):
        conn = get_connection()
        cursor = conn.cursor()
        
        
        query = "INSERT INTO datoscorporales (usuario_id, altura , peso) VALUES (%s, %s ,%s)"
        
        try:
            cursor.execute(query, (user_id, altura, peso))
            conn.commit()
            
            return {
                "success": True
            }
        
        except Exception as e:
            return {
                "success": "False",
                "error": str(e)
            }
        
        

    @staticmethod
    def get_datecorporal(user_id: int):
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = "SELECT * FROM datoscorporales WHERE usuario_id = %s"
        
            cursor.execute(query,(user_id,))

            resultado = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "data-corporal": resultado
            }
            
        except Exception as e:
            
            cursor.close()
            conn.close()
            
            return {
                "success": False,
                "error": str(e)
            }
        
        
        
        
    @staticmethod
    def add_salud_corporal(user_id: int, nombre: str, fecha: str):
        """Agrega de una enfermedad"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO saludcorporal (usuario_id, enfermedad_corporal, fecha_padecimiento)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (user_id, nombre, fecha))
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()   
        
        
        
        
        
    @staticmethod
    def get_salud_corporal(user_id: int):
        """Obtiene todas las enfermedades de un usuario"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT id, enfermedad_corporal as nombre, fecha_padecimiento
            FROM saludcorporal
            WHERE usuario_id = %s
            ORDER BY fecha_padecimiento DESC
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error: {e}")
            return []
        finally:
            cursor.close()
            conn.close()    
        
        
        
    @staticmethod
    def delete_salud_corporal(user_id: int, enfermedad_id: int):
        """
        Elimina una enfermedad específica.
        Verifica que pertenezca al usuario por seguridad.
        """
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        DELETE FROM saludcorporal 
        WHERE id = %s AND usuario_id = %s
        """

        try:
            cursor.execute(query, (enfermedad_id, user_id))
            conn.commit()

            if cursor.rowcount == 0:
                return {"success": False, "error": "Enfermedad no encontrada"}

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

       
    @staticmethod
    def add_salud_alimenticia(user_id: int, nombre: str):
        """Agrega una condición alimenticia"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO saludalimenticia (usuario_id, enfermedad_alimenticia)
            VALUES (%s, %s)
            """
            cursor.execute(query, (user_id, nombre))
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()       
          
         

    @staticmethod
    def get_salud_alimenticia(user_id: int):
        """Obtiene todas las condiciones alimenticias de un usuario"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT id, enfermedad_alimenticia as nombre
            FROM saludalimenticia
            WHERE usuario_id = %s
            ORDER BY id
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete_salud_alimenticia(user_id: int, enfermedad_id: int):
        """Elimina una condición alimenticia específica"""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        DELETE FROM saludalimenticia 
        WHERE id = %s AND usuario_id = %s
        """
        
        try:
            cursor.execute(query, (enfermedad_id, user_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "Enfermedad no encontrada"}
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()
        
                
    
    @staticmethod
    def get_datos_corporales(user_id: int):
        """Obtiene peso y altura del usuario"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT peso, altura FROM datoscorporales 
                WHERE usuario_id = %s 
                ORDER BY id DESC LIMIT 1
            """, (user_id,))
            return cursor.fetchone()
        
        except:
            return False
        finally:
            cursor.close()
            conn.close()
            
            
            

    @staticmethod
    def save_objetivo(user_id: int, objetivo: str):
        """Guarda o actualiza el objetivo de peso"""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO objetivo (usuario_id, objetivo_peso) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE objetivo_peso = VALUES(objetivo_peso)
        """
        
        try:
            cursor.execute(query, (user_id, objetivo))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()




    @staticmethod
    def save_meta_nutricional(user_id: int, metas: dict):
        """Guarda o actualiza la meta nutricional"""
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO metanutricional (usuario_id, calorias, proteinas, grasas, carbohidratos, azucares) 
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            calorias = VALUES(calorias),
            proteinas = VALUES(proteinas),
            grasas = VALUES(grasas),
            carbohidratos = VALUES(carbohidratos),
            azucares = VALUES(azucares)
        """

        try:
            cursor.execute(query, (
                user_id,
                metas["calorias"],
                metas["proteinas"],
                metas["grasas"],
                metas["carbohidratos"],
                metas["azucares"]
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()




    @staticmethod
    def get_objetivo(user_id: int):
        """Obtiene el objetivo del usuario"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT objetivo_peso FROM objetivo 
                WHERE usuario_id = %s
            """, (user_id,))
            return cursor.fetchone()
        
        finally:
            cursor.close()
            conn.close()

    
    @staticmethod
    def get_meta_nutricional(user_id: int):
        """Obtiene la meta nutricional del usuario"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT calorias, proteinas, grasas, carbohidratos, azucares 
                FROM metanutricional 
                WHERE usuario_id = %s
            """, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
            
            
            
            
    @staticmethod 
    def post_no_objetivo(user_id: int):
        # guardar todo 0.00 en metas nutricionales 
        # para cuando ponga objetivo "niguno o personalizado"
        conn = get_connection()
        cursor = conn.cursor()
        
        
        try :
            query = ("""
                INSERT INTO metanutricional (usuario_id, calorias, proteinas, grasas, carbohidratos, azucares) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                           """)
            cursor.execute(query,(
                user_id,
                0.00,
                0.00,
                0.00,
                0.00,
                0.00
            ))
            conn.commit()
            
            return True
            
        except:
            return False
            
            
            
        finally:
            if cursor:
                cursor.close()
                
            if conn:
                conn.close()
            
        
            
            
    @staticmethod
    def patch_meta_nutricional(user_id: int, metas: dict):
        """Guarda o actualiza la meta nutricional"""
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        UPDATE metanutricional SET calorias = %s, proteinas= %s, grasas= %s, carbohidratos= %s, azucares = %s WHERE usuario_id = %s
        """

        try:
            cursor.execute(query, (
                metas["calorias"],
                metas["proteinas"],
                metas["grasas"],
                metas["carbohidratos"],
                metas["azucares"],
                user_id
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()    
            

        
            
            