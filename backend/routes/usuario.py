from fastapi import APIRouter, Header, HTTPException
from utils.security import VerifyExpiredToken
from pydantic import BaseModel
from typing import List
from enum import Enum
from models.usuario_model import UsuarioModel
from services.nutricion_service import NutricionService



router = APIRouter()

class UsuarioUpdateRequest(BaseModel):
    apellido : str | None = None
    nombre : str | None = None
    sexo : str | None = None
    fecha_nacimiento: str | None = None
    num_telefono: str | None = None
    
class UsuarioDateCorporal(BaseModel):
    altura: float
    peso : float
    
    
    
class UsuarioUpdateDateCorporal(BaseModel):
    #su valor por defecto es None y si viene un dato tiene que ser
    #float o None
    altura: float | None = None
    peso: float | None = None
    

#para decirle que tiene que ser una lista
#que dentro de ella guarde la estructura
# que contenga los campos nombre formato string
# y fecha padecimiento string
class EnfermedadItem(BaseModel):
    nombre: str
    fecha: str  # YYYY-MM-DD

class SaludCorporalRequest(BaseModel):
    enfermedades: List[EnfermedadItem]    




class EnfermedadAlimenticiaItem(BaseModel):
    nombre: str

class SaludAlimenticiaRequest(BaseModel):
    enfermedades: List[EnfermedadAlimenticiaItem]


class ObjetivoPesoEnum(str, Enum):
    BAJAR = "bajar"
    SUBIR = "subir"
    MANTENER = "mantener"
    NINGUNO = "ninguno"

class ObjetivoPesoRequest(BaseModel):
    objetivo: ObjetivoPesoEnum
    
    
class MetaPersonalizada(BaseModel):
    calorias : float
    proteinas : float
    grasas : float
    carbohidratos : float
    azucares : float
    
    

class GuardarResultadosNutricionalesVision(BaseModel):
    nombre: str | None = None
    calorias : float | None = None
    proteinas : float | None = None
    grasas : float | None = None
    carbohidratos : float | None = None
    azucares : float | None = None
    guardar : bool | None = None # es para saber si restar o no al plan diario los macronutrientes


@router.post("/me/meta-nutricional/vision", summary= "Guardar resultados nutricionales de la vision") # Hecho
async def post_vision_meta(datos: GuardarResultadosNutricionalesVision, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    
    user_id = payload["data"]["id"]

    if datos.guardar == None or datos.guardar == False:
        raise HTTPException(500, "El campo guardar es obligatorio y para guardar los datos debe ser true")
        
        
    # si guardar es true, entonces se guardan las macros en la DB
    resultado = UsuarioModel.guardar_y_descontar_macros(user_id, datos.nombre ,datos.calorias, datos.proteinas, datos.grasas, datos.carbohidratos, datos.azucares)
    

    if not resultado:
        raise HTTPException(401, "Error al guardar los datos en la DB")
    
    return {
        "success": True,
        "message": "Datos guardados correctamente en la DB"
    }




@router.patch("/me/meta-nutricional/ninguno", summary= "Guardar datos personalizados en la DB")
async def patch_ninguno_meta(datos: MetaPersonalizada, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    
    user_id = payload["data"]["id"]

    
    metas = {
        "calorias": datos.calorias,
        "proteinas": datos.proteinas,
        "grasas": datos.grasas,
        "carbohidratos": datos.carbohidratos,
        "azucares": datos.azucares 
    }
    
    resultado = UsuarioModel.patch_meta_nutricional(user_id,metas)
    
    if not resultado:
        raise HTTPException(401, "Error al guardar los datos en la DB")
    
    return {
        "success": True,
        "message": "Datos guardados correctamente en la DB"
    }
    
    
    
    
    
    
    
@router.post("/me/meta-nutricional/ninguno", summary = "Guardar 0.00 en MN para cuando objetivo es Ninguno") #Hecho
async def post_ninguno_meta(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    
    user_id = payload["data"]["id"]
    
    resultado = UsuarioModel.post_no_objetivo(user_id)
    
    if not resultado:
        raise HTTPException(401, "Error al guardar los datos en la DB")
        
    return {
        "success": True,
        "message": "Datos guardados correctamente"
    }





@router.get("/me/objetivo-peso", summary="Obtener objetivo de peso")
async def get_objetivo_peso(authorization: str = Header(...)):
     # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    
    
    
    
    user_id = payload["data"]["id"]
    
    objetivo = UsuarioModel.get_objetivo(user_id)
    
    return {
        "success": True,
        "objetivo": objetivo["objetivo_peso"] if objetivo else "ninguno"
    }





@router.get("/me/meta-nutricional", summary="Obtener meta nutricional")
async def get_meta_nutricional(authorization: str = Header(...)):
   
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    user_id = payload["data"]["id"]
    
    metas = UsuarioModel.get_meta_nutricional(user_id)
    
    if not metas:
        raise HTTPException(404, "No hay meta nutricional calculada")
    
    return {
        "success": True,
        "metas": metas
    }




@router.post("/me/objetivo-peso", summary="Guardar objetivo de peso") # Hecho
async def save_objetivo_peso(
    datos: ObjetivoPesoRequest,
    authorization: str = Header(...)
):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    
    # 2. Obtener datos del usuario
    usuario = UsuarioModel.get_by_id(user_id)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    
    # 3. Obtener datos corporales
    datos_corporales = UsuarioModel.get_datos_corporales(user_id)
    if not datos_corporales:
        raise HTTPException(400, "Primero debe ingresar peso y altura")
    
    
    
    
    # 4. Calcular edad
    edad = NutricionService.calcular_edad(usuario["fecha_nacimiento"])
    
    # 5. Calcular metas nutricionales
    metas = NutricionService.calcular_metas(
        objetivo=datos.objetivo,
        sexo=usuario["sexo"],
        peso=datos_corporales["peso"],
        altura=datos_corporales["altura"],
        edad=edad
    )
    
    # 6. Guardar objetivo
    UsuarioModel.save_objetivo(user_id, datos.objetivo)
    
    # 7. Guardar meta nutricional
    UsuarioModel.save_meta_nutricional(user_id, metas)
    
    return {
        "success": True,
        "objetivo": datos.objetivo,
        "metas": metas,
        "mensaje": "Objetivo y metas nutricionales calculadas"
    }






@router.delete("/me/salud-alimenticia/{enfermedad_id}", summary="Eliminar enfermedad alimenticia")
async def delete_salud_alimenticia(
    enfermedad_id: int,
    authorization: str = Header(...)
):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    
    # 2. Eliminar enfermedad
    resultado = UsuarioModel.delete_salud_alimenticia(user_id, enfermedad_id)
    
    if not resultado["success"]:
        raise HTTPException(404, resultado.get("error", "Enfermedad no encontrada"))
    
    return {
        "success": True,
        "mensaje": "Condición alimenticia eliminada",
        "id": enfermedad_id
    }



@router.get("/me/salud-alimenticia", summary="Obtener enfermedades alimenticias")
async def get_salud_alimenticia(authorization: str = Header(...)):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    
    # 2. Obtener enfermedades
    enfermedades = UsuarioModel.get_salud_alimenticia(user_id)
    
    return {
        "success": True,
        "enfermedades": enfermedades
    }



@router.post("/me/salud-alimenticia", summary="Guardar enfermedades alimenticias") #Hecho
async def save_salud_alimenticia(
    datos: SaludAlimenticiaRequest,
    authorization: str = Header(...)
):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    

    
    # 3. Insertar las nuevas una por una
    for enfermedad in datos.enfermedades:
        resultado = UsuarioModel.add_salud_alimenticia(
            user_id,
            enfermedad.nombre
        )
        if not resultado["success"]:
            raise HTTPException(500, f"Error guardando: {enfermedad.nombre}")
    
    return {
        "success": True,
        "mensaje": f"Se guardaron {len(datos.enfermedades)} condiciones alimenticias",
        "cantidad": len(datos.enfermedades)
    }




@router.delete("/me/salud-corporal/{enfermedad_id}", summary="Eliminar problema corporal")
async def delete_salud_corporal(
    enfermedad_id: int,
    authorization: str = Header(...)
    ):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    
    # 2. Eliminar la enfermedad (verificando que pertenezca al usuario)
    resultado = UsuarioModel.delete_salud_corporal(user_id, enfermedad_id)
    
    if not resultado["success"]:
        raise HTTPException(404, resultado.get("error", "Enfermedad no encontrada"))
    
    return {
        "success": True,
        "mensaje": "Condición de salud eliminada",
        "id": enfermedad_id
    }
    
    
    
@router.post("/me/salud-corporal", summary="Guardar todos los problemas corporles") # Hecho
async def save_salud_corporal(
    datos: SaludCorporalRequest,
    authorization: str = Header(...)
):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    

    
    # 3. Insertar las nuevas enfermedades
    # las insertamos una por una para que esten
    # en diferentes id separadas para mas control
    for enfermedad in datos.enfermedades:
        resultado = UsuarioModel.add_salud_corporal(
            user_id,
            enfermedad.nombre,
            enfermedad.fecha
        )
        if not resultado["success"]:
            raise HTTPException(500, f"Error guardando: {enfermedad.nombre}")
    
    return {
        "success": True,
        "mensaje": f"Se guardaron {len(datos.enfermedades)} condiciones",
        "cantidad": len(datos.enfermedades)
    }
    
    
    

@router.get("/me/salud-corporal", summary="Obtener todas las enfermedades corporal")
async def get_salud_corporal(authorization: str = Header(...)):
    # 1. Verificar token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    user_id = payload["data"]["id"]
    
    # 2. Obtener enfermedades
    enfermedades = UsuarioModel.get_salud_corporal(user_id)
    
    return {
        "success": True,
        "enfermedades": enfermedades
    }
    
    
    
   
@router.get("/me/datos-corporales", summary= "Devolver Datos corporales")
async def get_datecorporal(authorization: str = Header(...)): 
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    
    if payload.get("expired"):
        raise HTTPException(401, "El token expiro")
    
    
    resultado = UsuarioModel.get_datecorporal(payload["data"]["id"])
    
    
    if "error" in resultado:
        raise HTTPException(401, f"Error: {resultado["error"]} ")
    
    return resultado

 
    
    
    
    

@router.post("/me/datos-corporales", summary= "Guardar datos corporales primera vez/no SET") # Hecho
async def date_corporal(datos: UsuarioDateCorporal, authorization: str = Header(...)):
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    
    if payload.get("expired"):
        raise HTTPException(401, "El token expiro")
    
    resultado = UsuarioModel.savedDateCorporal(payload["data"]["id"], datos.altura, datos.peso)
    
    if not resultado["success"]:
        raise HTTPException(500, "Error al guardar los datos")
    
    
    return {
        "success": True,
        "message": "Se actualizaron correctamente los datos"
    }
    
  
  
  
@router.patch("/me/datos-corporales", summary = "Actualizar Datos corporales") 
async def update_datecorporal(datos: UsuarioUpdateDateCorporal, authorization: str = Header(...)):
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    
    if payload.get("expired"):
        raise HTTPException(401, "El token expiro")
    


    #reconstruir datos
    campos = {}
    if datos.altura is not None:
        campos["altura"] = datos.altura
        
    if datos.peso is not None:
        campos["peso"] = datos.peso
    
    if not campos:
        raise HTTPException(400, "No se enviaron datos")
    
    
    #obtener id usuario
    user_id = payload["data"].get("id")
    
    #ACTUALIZAR EN LA DB
    resultado = UsuarioModel.updateDateCorporal(user_id, campos)
    
    if not resultado:
        raise HTTPException(500, "Error al actualizar Datos")
    
    
    return {
        "success": True,
        "message": "Datos actualizados correctamente"
    }
    

@router.patch("/me", summary = "Actualizar datos del usuario /solo tabla usuario(nombre,num_tel...)")
async def update_usuario(datos: UsuarioUpdateRequest, authorization: str = Header(...)):
    
    #Verificar si la peticion viene con el token
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if not payload:
        raise HTTPException(401, "Token invalido o expirado")
    
    
    #Obtener user_id del payload:
    user_id = payload["data"].get("id")
    
    
    
    #construir datos a actualizar
    campos = {}
    if datos.apellido is not None:
        campos["apellido"] = datos.apellido
        
    if datos.nombre is not None:
        campos["nombre"] = datos.nombre
        
    if datos.sexo is not None:
        campos["sexo"] = datos.sexo
    
    if datos.fecha_nacimiento is not None:
        campos["fecha_nacimiento"] = datos.fecha_nacimiento
        
    if datos.num_telefono is not None:
        campos["num_telefono"] = datos.num_telefono
        
        
    if not campos:
        raise HTTPException(400, "No se enviaron los datos")
    
    
    #actualizar en la BD
    
    resultado = UsuarioModel.update(user_id, campos)
    
    if not resultado:
        raise HTTPException(500, "Error al actualizar")
    
    #obtener usuario actualizado
    usuario = UsuarioModel.get_by_id(user_id)
    
    return{
        "user": usuario
    }
    
    
    
    
    
@router.get("/me", summary = "VerficarJWT/Devuelve Datos de usuario") # Hecho 
# este tomara del header el campo authorization
# como lo sabe? lo compara con el nombre de la variable
# los 3 puntos indica que el campo es obligatorio
async def get_me(authorization: str = Header(...)):
    
    # esta comprobando (si authorization no empieza con "Bearer ")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Formato de token invalido. Use: Bearer <token>"
        )
    
    
    token = authorization.replace("Bearer ", "")
    
    resultado = VerifyExpiredToken.verify_token(token)
    
    if "error" in resultado:
        raise HTTPException(
            status_code=401,
            detail=resultado["error"]
        )
        
        
    
    if resultado.get("expired"):
        raise HTTPException(
            status_code=401,
            detail="Token expirado"
        )
        
        
    return {
        "activo": True,
        "user" : resultado
        
    }
        
    
    