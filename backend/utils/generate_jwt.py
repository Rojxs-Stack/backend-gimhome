from jose import jwt
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta,timezone
import os



class ValidateDatesUser(BaseModel):
    user_id : int
    email: EmailStr
    
    

class GenerateJwt:
    
    SECRET_KEY= os.getenv("JWT_SECRET_KEY")
    ALGORITHM= os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES= 60 * 24 * 7
    
    
    @classmethod
    async def create_jwt(cls, user_id: ValidateDatesUser, email: ValidateDatesUser):
        
        try:
    
            #GENERAR EL TOKEN CON EXPIRACION
    
            expire = datetime.now(timezone.utc) + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode = {
                "user_id": user_id,
                "email": email,
                "exp": expire
                }
            access_token = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
            
            
            return {
                    "success": True ,
                    "access_token": access_token
                    }
            
        except Exception as e:
            return{
                "success": False,
                "error": str(e)
            }
