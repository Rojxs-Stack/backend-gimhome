#  ACA VA TODA LA LOGICA DE GOOGLE

from models.usuario_model import UsuarioModel
from utils.generate_jwt import GenerateJwt

# Esta es la que hace el trabajo pesado de verificación.
# Cuando un usuario se loguea con Google en su celular o 
# navegador, Google le da un "Token de Identidad" 
# (un código larguísimo y encriptado).
# Tu API recibe ese código, y id_token sirve para 
# "desencriptarlo" y verificar que la firma digital
# sea auténtica de Google y no un código inventado por un hacker.
# Qué te devuelve: Si es válido, te entrega un 
# diccionario con los datos reales: email, nombre, foto, etc.
from google.oauth2 import id_token


# Esta es el medio de transporte.
# Para que tu API pueda verificar el token, a veces necesita
# "llamar" a los servidores de Google para pedirles las llaves
# públicas actuales.
# requests (en este contexto de Google Auth) es el motor 
# que realiza esa comunicación segura por internet entre 
# tu servidor y el de Google.
from google.auth.transport import requests

import os


# CONTROLADOR PAR AUTENTICACION
class AuthController:
    
    #este es el cliente ID que obtenemos de google cloud console
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    
    
    #VERIFICA TOKEN DE GOOGLE Y AUNTENTICA/CREA USUARIO
    # VERIFICA SI EL USUARIO YA EXISTE EN LA BASE DE DATOS PERO ESTA VOLVIENDO
    # A INGRESAR DIGAMOS SOLO SE ACTUALIZAN LOS DATOS (NOMBRE Y GOOGLE_ID por si los cambio)
    # O SI NO EXISTE PUES CREA UN USUARIO NUEVO, PERO PRIMERO CONSULTA SI 
    # EL USUARIO QUE INTENTA INGRESAR EXISTE
    @classmethod
    async def google_login(cls, token_google):
        
        try:
            
            #verificamos que el token sea valido con google
            #  Es el "notario". Recibe el token que mandó el
            # frontend y comprueba que la firma digital sea
            # auténtica de Google. Si alguien inventó el token 
            # o lo modificó, esta función "explota" y da un error.
            idinfo = id_token.verify_oauth2_token(
                
                # Es la credencial que el usuario consiguió al 
                # loguearse en su celular/navegador
                token_google, 
                # Es el "mensajero". Como las llaves de 
                # seguridad de Google cambian cada tanto,
                # esta parte le dice a tu backend: "Andá a 
                # internet y bajate las llaves públicas actuales 
                # de Google para comparar si este token es real".
                requests.Request(),
                
                # Es el "candado". Verifica que el token fue
                # emitido específicamente para tu app NutrieScan 
                # y no para otra aplicación (como Spotify o Instagram).
                # Si el token es de otra app, lo rechaza.
                cls.GOOGLE_CLIENT_ID
            )
            
            
            
            #datos que vienen de google
            email = idinfo['email']
            nombre = idinfo.get('name', '')
            google_id = idinfo['sub']
            foto_url = idinfo.get('picture', '')
            
            
            
            #verificar si el usuario ya existe
            usuario_existente = UsuarioModel.get_by_email(email)
        
        
        
            if usuario_existente:
                # si existe pero no tiene google_id lo actualizamos
                if not usuario_existente.get('google_id'):
                    UsuarioModel.update_google_data(
                        usuario_existente['id'],
                        nombre,
                        google_id,
                        foto_url 
                    )

                new_token_jwt = await GenerateJwt.create_jwt(usuario_existente['id'], email)
                
                if not new_token_jwt["success"]:
                    return {
                        "success": False,
                        "error": new_token_jwt["error"]
                    }
                  
                    
                return {
                    "success": True,
                    "usuario": {
                        "id" : usuario_existente["id"],
                        "email" : email,
                        "nombre" : nombre,
                        "foto_url": foto_url,
                        "tokenjwt": new_token_jwt["access_token"],
                        "nuevo": False
                    }
                }


                
                
                
                
            else: 
                # CREAR NUEVO USUARIO
                resultado = UsuarioModel.create_from_google(
                    email= email,
                    nombre= nombre,
                    google_id = google_id,
                    foto_url = foto_url
                )
                
                
                


                if not resultado["success"]:
                    return{
                        "success": False,
                        "error": resultado["error"]
                    }
                    
                token_jwt = await GenerateJwt.create_jwt(resultado['user_id'], email)
                
                
                if not token_jwt["success"]:
                    return{
                        "success": False,
                        "error": token_jwt["error"]
                    }
                    
                return {
                    "success": True,
                    "usuario": {
                        "id": resultado["user_id"],
                        "email": email,
                        "nombre": nombre,
                        "foto_url": foto_url,
                        "tokenjwt": token_jwt["access_token"],
                        "nuevo": True
                    }
                }
                
                
        except ValueError as e:
            
            #token invalido
            return {
                "success": False,
                "error": "Token de Google Invalido"
            }
            
        except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
                
                
                    
                








