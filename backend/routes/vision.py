from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from utils.security import VerifyExpiredToken
from services.vision_service import VisionService
from pydantic import BaseModel, ValidationError
from utils.image_optimizer import optimizar_para_vision_comida
from utils.cuota_diaria import CuotaDiariaService  # 🆕 Importar
#import toon

router = APIRouter()


class ResultadoNutricional(BaseModel):
    nombre: str  
    calorias: float
    proteinas: float
    grasas: float
    carbohidratos: float
    azucares: float


@router.post("/analizar_imagen")
async def analizar_imagen(authorization: str = Header(...), file: UploadFile = File(...)):
    
    # ========== PASO 1: VALIDACIÓN DE AUTENTICACIÓN ==========
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
    
    # ========== PASO 2: LECTURA DE IMAGEN ==========
    imagen_bytes = await file.read()
    
    # ========== PASO 3: OPTIMIZACIÓN INTELIGENTE DE IMAGEN ==========
    imagen_optimizada, metadatos = optimizar_para_vision_comida(imagen_bytes)
    
    print(f"[OPTIMIZACION] {metadatos}")
    
    # ========== PASO 4: ANÁLISIS CON IA ==========
    resultado_raw = VisionService.analizar_imagen(imagen_optimizada)

    if isinstance(resultado_raw, dict) and "error" in resultado_raw:
        raise HTTPException(500, resultado_raw["error"])

    # ========== PASO 5 Y 6: DECODIFICACIÓN TOON + VALIDACIÓN ==========
    try:
        # Parseo manual de TOON (sin depender de la librería toon)
        # Formato esperado: datos[1]{nombre,calorias,proteinas,grasas,carbohidratos,azucares}: "nombre",num,num,num,num,num
        
        if ": " not in resultado_raw:
            raise HTTPException(500, "Formato TOON inválido: falta ':'")
        
        # Extraer los valores después de ": "
        valores_str = resultado_raw.split(": ", 1)[1].strip()
        
        # Buscar el nombre entre comillas dobles
        if not valores_str.startswith('"'):
            raise HTTPException(500, "Formato inválido: el nombre debe empezar con comillas dobles")
        
        # Encontrar la comilla de cierre del nombre
        primer_cierre = valores_str.find('"', 1)
        if primer_cierre == -1:
            raise HTTPException(500, "Formato inválido: no se encontró la comilla de cierre del nombre")
        
        nombre = valores_str[1:primer_cierre]
        
        # Extraer los números (lo que viene después de ", ")
        resto = valores_str[primer_cierre + 1:].strip()
        if not resto.startswith(","):
            raise HTTPException(500, "Formato inválido: falta la coma después del nombre")
        
        numeros_str = resto[1:].strip()  # Sacar la coma inicial
        
        # Dividir los números
        partes = [p.strip() for p in numeros_str.split(",")]
        
        if len(partes) != 5:
            raise HTTPException(500, f"Se esperaban 5 números, se recibieron {len(partes)}")
        
        # Convertir a float
        calorias = float(partes[0])
        proteinas = float(partes[1])
        grasas = float(partes[2])
        carbohidratos = float(partes[3])
        azucares = float(partes[4])
        
        # Construir el objeto
        info_nutricional = {
            "nombre": nombre.strip(),
            "calorias": calorias,
            "proteinas": proteinas,
            "grasas": grasas,
            "carbohidratos": carbohidratos,
            "azucares": azucares
        }
        
        data = ResultadoNutricional(**info_nutricional)

        es_comida_detectada = data.calorias >= 0.0
        
        if not es_comida_detectada:
            print(f"[INFO] Imagen sin comida detectada. User: {user_id}")
        
        # ========== DESCONTAR ESCANEO (SOLO SI TODO SALIÓ BIEN) ==========
        nuevo_total = CuotaDiariaService.incrementar_escaneo(user_id)
        escaneos_restantes = limite - nuevo_total
            
        # ========== PASO 7: RESPUESTA ==========

        print(f"""
            "resultado": {data},
            "es_comida_detectada": {es_comida_detectada},
            "escaneos_hoy": {nuevo_total},
            "escaneos_restantes": {escaneos_restantes}
        """)
        
        return {
            "resultado": data,
            "es_comida_detectada": es_comida_detectada,
            "escaneos_hoy": nuevo_total,
            "escaneos_restantes": escaneos_restantes
        }
        
    except (Exception, ValidationError) as e:
        # Si falla, NO descontamos el escaneo
        print(f"[ERROR] Falló el parseo TOON: {str(e)}")
        print(f"[ERROR] resultado_raw: {resultado_raw}")
        raise HTTPException(500, f"Error procesando formato TOON: {str(e)}")