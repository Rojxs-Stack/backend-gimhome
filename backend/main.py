# ESTE ES EL PUNTO DE ENTRADA DE TODAS
# LAS PETICIONES

from fastapi import FastAPI
from routes import auth, usuario, vision, recetas
from fastapi.middleware.cors import CORSMiddleware

# ESTO ES PARA QUE SE MUESTRE DE MANERA PROFESIONAL EN LA DOCUMENTACION
# AUTOMATICA Y ADEMAS CREAMOS LA INSTANCIA DE FASTAPI EL CONSTRUCTOR
# DE MI APLICACION
app = FastAPI(
    title = "NutrieScan API",
    description= "API profesional para app de nutricion",
    version="1.0.0",
    docs_url="/docs", #Swagger UI
    redoc_url="/redoc" #Documentacion alternativa
    
)


# configuracion de CORS
# prueba con html,css y js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las fuentes (en producción, especificar dominios)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router, prefix="/auth", tags=["Autenticacion"])
app.include_router(usuario.router, prefix="/usuarios" ,  tags=["Operaciones de Usuario"])
app.include_router(vision.router, prefix="/vision", tags=["Vision"])
app.include_router(recetas.router, prefix="/recetas", tags=["Recetas"])



# REGISTRAR RUTAS
@app.get("/")
def root():
    return {
        "nombre": "NutrieScan API",
        "version": "1.0.0",
        "documentacion": "/docs",
        # indica que la API funciona y se puede operar
        "estado": "operacional"
    }


# endpoin para verificar que la API funciona
@app.get("/health", summary= "Test del Endpoint")
def health_check():
    return {"status": "ok", "database": "conectada"}


















