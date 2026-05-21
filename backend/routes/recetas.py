from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Form
from utils.security import VerifyExpiredToken
from services.recetas_service import RecetasService
from pydantic import BaseModel
from typing import List
from utils.image_optimizer import optimizar_para_vision_comida
from utils.cuota_diaria import CuotaDiariaService 
import json

router = APIRouter()

# ========== FUNCIÓN AUXILIAR DE PARSEO TOON ==========
def _split_respetando_comillas(texto: str):
    """
    Divide una cadena por comas, pero respetando lo que está entre comillas dobles.
    Ejemplo: 'hola,"mundo, cruel",123' → ['hola', '"mundo, cruel"', '123']
    """
    partes = []
    actual = ""
    entre_comillas = False
    
    for char in texto:
        if char == '"':
            entre_comillas = not entre_comillas
            actual += char
        elif char == ',' and not entre_comillas:
            partes.append(actual.strip())
            actual = ""
        else:
            actual += char
    
    if actual.strip():
        partes.append(actual.strip())
    
    return partes


def _parsear_toon_recetas(resultado_raw: str):
    """
    Parsea respuesta TOON de recetas a diccionario Python.
    Si detecta "NO_ALIMENTOS", devuelve valores seguros por defecto.
    """
    if ": " not in resultado_raw:
        raise ValueError("Formato TOON inválido: falta ':'")
    
    # Extraer valores después de ": "
    valores_str = resultado_raw.split(": ", 1)[1].strip()
    
    # Dividir respetando comillas
    partes = _split_respetando_comillas(valores_str)
    
    if len(partes) != 9:
        raise ValueError(f"Se esperaban 9 campos, se recibieron {len(partes)}")
    
    # Función interna para limpiar comillas
    def _limpiar(valor: str) -> str:
        valor = valor.strip()
        if valor.startswith('"') and valor.endswith('"'):
            return valor[1:-1]
        return valor
    
    nombre_receta = _limpiar(partes[0])
    
    # 🆕 Detectar caso "NO_ALIMENTOS" (todos los valores son -1 o -1.0)
    if nombre_receta == "NO_ALIMENTOS":
        return {
            "datos": [{
                "nombre_receta": "No se detectaron alimentos",
                "calorias_totales": -1.0,
                "proteinas_totales": -1.0,
                "grasas_totales": -1.0,
                "carbohidratos_totales": -1.0,
                "ingredientes_usados": [],      # Lista vacía para que Pydantic valide
                "instrucciones": "",
                "objetivo_alcanzado": False,
                "maximo_alcanzable": -1.0
            }]
        }
    
    # Si no es "NO_ALIMENTOS", continuar con el parseo normal
    # Parsear ingredientes (viene con comillas escapadas dobles)
    ingredientes_str = _limpiar(partes[5])
    ingredientes_str = ingredientes_str.replace('""', '"')
    ingredientes_usados = json.loads(ingredientes_str)
    
    return {
        "datos": [{
            "nombre_receta": nombre_receta,
            "calorias_totales": float(partes[1].strip()),
            "proteinas_totales": float(partes[2].strip()),
            "grasas_totales": float(partes[3].strip()),
            "carbohidratos_totales": float(partes[4].strip()),
            "ingredientes_usados": ingredientes_usados,
            "instrucciones": _limpiar(partes[6]),
            "objetivo_alcanzado": partes[7].strip().lower() == "true",
            "maximo_alcanzable": float(partes[8].strip())
        }]
    }

class IngredienteUsado(BaseModel):
    nombre: str
    cantidad: str


class ResultadoReceta(BaseModel):
    nombre_receta: str
    calorias_totales: float
    proteinas_totales: float
    grasas_totales: float
    carbohidratos_totales: float
    ingredientes_usados: List[IngredienteUsado]
    instrucciones: str
    objetivo_alcanzado: bool
    maximo_alcanzable: float


@router.post("/generar_receta")
async def generar_receta(
    authorization: str = Header(...),
    calorias_objetivo: float = Form(...),
    file: UploadFile = File(...)
):
    # ========== VALIDACIÓN DE TOKEN ==========
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato invalido")
    
    token = authorization.replace("Bearer ", "")
    payload = VerifyExpiredToken.verify_token(token)
    
    if "error" in payload:
        raise HTTPException(401, payload["error"])
    if payload.get("expired"):
        raise HTTPException(401, "Token expirado")
    
    #  Obtener user_id del payload
    user_id = payload["data"].get("id")
    
     
    if not user_id:
        raise HTTPException(401, "Token no contiene user_id")
    
    
    # ========== 🆕 VERIFICAR CUOTA DIARIA ==========
    puede, actuales, limite = CuotaDiariaService.puede_escanear(user_id)
    
    if not puede:
        raise HTTPException(
            429,
            f"Límite diario alcanzado. Has usado {actuales}/{limite} escaneos hoy. Vuelve mañana."
        )
    
    # ========== OPTIMIZAR IMAGEN ==========
    imagen_bytes = await file.read()
    imagen_optimizada, metadatos = optimizar_para_vision_comida(imagen_bytes)
    print(f"[OPTIMIZACION] {metadatos}")
    
    # ========== GENERAR RECETA ==========
    resultado_raw = RecetasService.generar_receta(imagen_optimizada, calorias_objetivo)
    
    if isinstance(resultado_raw, dict) and "error" in resultado_raw:
        raise HTTPException(500, resultado_raw["error"])
    
    # ========== DECODIFICAR TOON ==========
    try:
         # Usar parser manual propio (la librería 'toon' fallaba)
        datos_toon = _parsear_toon_recetas(resultado_raw)
        lista = datos_toon.get("datos", [])
        
        if not lista:
            raise HTTPException(500, "La IA no devolvió la clave 'datos'")
        
        info_receta = lista[0]
        
        data = ResultadoReceta(**info_receta)
        
        # ========== 🆕 DESCONTAR ESCANEO (SOLO SI TODO SALIÓ BIEN) ==========
        nuevo_total = CuotaDiariaService.incrementar_escaneo(user_id)
        escaneos_restantes = limite - nuevo_total
        
        print("RESPUESTA FINAL DEVUELVE A FRONTENED: ", data)
        
        return {
            "resultado": data,
            "mensaje": "¡Receta generada con éxito!" if data.objetivo_alcanzado else f"Máximo alcanzable: {data.maximo_alcanzable} kcal",
            "escaneos_hoy": nuevo_total,           # 🆕 Info para frontend
            "escaneos_restantes": escaneos_restantes  # 🆕 Info para frontend
        }
        
    except Exception as e:
        # Si falla, NO descontamos el escaneo
        raise HTTPException(500, f"Error procesando receta: {str(e)}")