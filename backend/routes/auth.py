# ACA DEFINIMOS LOS ENDPOINTS

from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel
from controllers.auth_controller import AuthController



router = APIRouter()


# MODELOS PYDANTIC PARA VALIDACION DE DATOS

# Definimos que formato tiene que ser el token
# que llega de la peticion
class GoogleTokenRequest(BaseModel):
    token: str

    
    
# Definimos la estructura de respuesta que devolveremos en JSON,
# en caso de que sea primera vez registrado o ya exista 
class GoogleLoginResponse(BaseModel):
    success: bool
    usuario: dict
    mensaje: str = None
    
    
@router.post(
    "/google", #hasta aca definimos que el endpoints solo acepta POST
    
    # Se asegura que la respuesta tenga  la estructura
    # de GoogleLoginResponse
    response_model= GoogleLoginResponse,
    # Si la operacion fue ejecutada con exito
    # Devolvera 200 Ok
    status_code= status.HTTP_200_OK,
    #para la documentacion
    summary="Iniciar sesion/resgistrarse con google"
)
#el body con los datos cae directamente aqui 
#y el base model los transforma en un objeto
#instanciado con nuestra clase
async def login_google(request: GoogleTokenRequest):
    # Endpoint para autenticación con Google
    #   Recibe el token de Google desde la app y:
    #   - Si el email NO existe: crea usuario nuevo
    #   - Si el email YA existe: vincula cuenta de Google
    
    resultado = await AuthController.google_login(request.token)
    
    if not resultado["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=resultado["error"]
        )
        
    return {
        "success": True,
        "usuario": resultado["usuario"],
        "mensaje": "Autenticacion Exitosa"
    }
    
    
# Endpoin de prueba para verificar que el router funciona
@router.get("/test")
def test():
    return {"mensaje": "Ruta de autenticacion funcionando"}
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    