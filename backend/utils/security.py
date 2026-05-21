from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from models.usuario_model import UsuarioModel
import os






class VerifyExpiredToken:
    
    
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    
    
    @classmethod
    def verify_token(cls,token: str):
        try:
            #el jwt desencriptado con los datos del usuario_id dentro y el email
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            
            data_user = UsuarioModel.get_by_email(payload["email"])
            
                
                
            return {
                "expired": False,
                "access_token": token,
                "data": {
                    "id": data_user["id"],
                    "nombre": data_user["nombre"],
                    "apellido": data_user["apellido"],
                    "sexo": data_user["sexo"],
                    "email": data_user["email"],
                    "foto_url": data_user["foto_url"],
                    "fecha_nacimiento": data_user["fecha_nacimiento"],
                    "num_telefono": data_user["num_telefono"]
                    
                }
                
            }
            
            
        # es la excepcion que devuelve jwt.decode cuando el jwt esta vencido
        except ExpiredSignatureError:
            return {
                "expired": True,
                "access_token": token
            }
        # excepcion cuando el token no es valido
        except JWTError:
            return {
                "success": False,
                "error": "Token invalido"
            }
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            