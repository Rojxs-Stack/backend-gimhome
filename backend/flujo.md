# Arquitectura y Flujo del Backend NutrieScan API

## Diagrama General del Sistema

```mermaid
graph TB
    subgraph "PUNTO DE ENTRADA"
        A["main.py<br/>(Instancia FastAPI)"]
    end

    subgraph "CONFIGURACION"
        B["FastAPI Config<br/>- Title: NutrieScan API<br/>- Version: 1.0.0<br/>- Docs: /docs<br/>- ReDoc: /redoc"]
    end

    subgraph "ROUTING"
        C["auth.router<br/>prefix: /auth"]
        D["usuario.router<br/>prefix: /usuarios"]
    end

    subgraph "ENDPOINTS RAIZ"
        E["GET /<br/>Health Check"]
        F["GET /health<br/>DB Connection Test"]
    end

    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
```

## Flujo Completo por Endpoint

### 1. AUTENTICACION CON GOOGLE ✓

```mermaid
graph TD
    subgraph "ENDPOINT: POST /auth/google"
        A["Cliente envía:<br/>{ token: string }"]
    end

    subgraph "RUTAS (auth.py)"
        B["@router.post<br/>- Valida estructura con<br/>GoogleTokenRequest Pydantic<br/>- response_model: GoogleLoginResponse<br/>- status_code: 200"]
        C["Llama AuthController.google_login<br/>con token_google"]
    end

    subgraph "CONTROLADOR AUTH (auth_controller.py)"
        D["AuthController.google_login<br/>metodo async classmethod"]
        E["id_token.verify_oauth2_token<br/>- Verifica firma digital Google<br/>- Valida contra GOOGLE_CLIENT_ID<br/>- Usa requests.Request() para<br/>conexion a servidores Google"]
        F["Extrae datos de Google:<br/>- email<br/>- nombre<br/>- google_id = idinfo[sub]<br/>- foto_url"]
    end

    subgraph "MODELO USUARIO (usuario_model.py)"
        G["UsuarioModel.get_by_email<br/>email parameter"]
        H{"¿Usuario existe?"}
        I["Rama SI: Usuario ya existe<br/>UsuarioModel.update_google_data<br/>Actualiza: nombre, google_id,<br/>foto_url, activo=1"]
        J["Rama NO: Usuario nuevo<br/>UsuarioModel.create_from_google<br/>INSERT tabla usuario"]
    end

    subgraph "TABLAS DATABASE"
        K["TABLA: usuario<br/>Campos:<br/>- id INT PRIMARY KEY AUTO<br/>- email VARCHAR UNIQUE<br/>- nombre VARCHAR<br/>- google_id VARCHAR<br/>- foto_url VARCHAR<br/>- activo BOOLEAN<br/>- fecha_nacimiento DATE<br/>- sexo VARCHAR<br/>- apellido VARCHAR<br/>- num_telefono VARCHAR"]
    end

    subgraph "JWT GENERATION (generate_jwt.py)"
        L["GenerateJwt.create_jwt<br/>- user_id<br/>- email"]
        M["Genera Token con JOSE<br/>- Payload: user_id, email, exp<br/>- Algoritmo: HS256<br/>- Expiracion: 7 días<br/>- Secret: JWT_SECRET_KEY"]
    end

    subgraph "RESPUESTA"
        N["Devuelve JSON:<br/>{<br/>  success: true,<br/>  usuario: {<br/>    id, email, nombre,<br/>    foto_url, tokenjwt,<br/>    nuevo: true|false<br/>  }<br/>}"]
    end

    A --> B --> C --> D --> E --> F --> G --> H
    H -->|SI| I
    H -->|NO| J
    I --> L
    J --> L
    L --> M
    G -.Query.-> K
    J -.INSERT.-> K
    I -.UPDATE.-> K
    M --> N
```

### 2. VERIFICAR JWT Y OBTENER DATOS USUARIO - GET /usuarios/me

```mermaid
graph TD
    subgraph "ENDPOINT: GET /usuarios/me"
        A["Cliente envía:<br/>Header: Authorization: Bearer token_jwt"]
    end

    subgraph "RUTAS (usuario.py)"
        B["@router.get /me<br/>- Verifica Bearer format<br/>- Extrae token quitando 'Bearer '"]
    end

    subgraph "SEGURIDAD (security.py)"
        C["VerifyExpiredToken.verify_token<br/>metodo classmethod"]
        D["jwt.decode(token,<br/>SECRET_KEY,<br/>algorithms=ALGORITHM)<br/>- Desencripta el JWT<br/>- Valida signatura<br/>- Extrae payload"]
        E{"¿Token válido?"}
        F["ExpiredSignatureError<br/>→ Retorna expired: true"]
        G["JWTError<br/>→ Retorna error message"]
    end

    subgraph "MODELO USUARIO (usuario_model.py)"
        H["UsuarioModel.get_by_email<br/>Con email del payload"]
        I["SELECT * FROM usuario<br/>WHERE email = %s<br/>cursor.fetchone()"]
    end

    subgraph "RESPUESTA EXITOSA"
        J["Retorna JSON:<br/>{<br/>  activo: true,<br/>  user: {<br/>    expired: false,<br/>    access_token: token,<br/>    data: {<br/>      id, nombre, apellido,<br/>      sexo, email,<br/>      foto_url,<br/>      fecha_nacimiento,<br/>      num_telefono<br/>    }<br/>  }<br/>}"]
    end

    A --> B --> C --> D --> E
    E -->|Válido| H --> I --> J
    E -->|Expirado| F
    E -->|Inválido| G
```

### 3. ACTUALIZAR PERFIL USUARIO - PATCH /usuarios/me

```mermaid
graph TD
    subgraph "ENDPOINT: PATCH /usuarios/me"
        A["Cliente envía:<br/>Header: Authorization<br/>Body: UsuarioUpdateRequest"]
        B["UsuarioUpdateRequest Model:<br/>- apellido: str | None<br/>- nombre: str | None<br/>- sexo: str | None<br/>- fecha_nacimiento: str | None<br/>- num_telefono: str | None"]
    end

    subgraph "VALIDACION TOKEN"
        C["Valida formato Bearer"]
        D["VerifyExpiredToken.verify_token"]
    end

    subgraph "CONSTRUCCION DINAMICA"
        E["Itera sobre datos recibidos<br/>Solo incluye campos NO NULL"]
        F["Construye diccionario<br/>campos = {<br/>  'apellido': valor,<br/>  'nombre': valor,<br/>  etc<br/>}"]
    end

    subgraph "MODELO USUARIO (usuario_model.py)"
        G["UsuarioModel.update<br/>- user_id<br/>- campos dict"]
        H["Genera UPDATE dinámico<br/>UPDATE usuario SET<br/>nombre = %s,<br/>apellido = %s,<br/>sexo = %s,<br/>fecha_nacimiento = %s,<br/>num_telefono = %s<br/>WHERE id = %s"]
    end

    subgraph "TABLA AFECTADA"
        I["TABLA: usuario<br/>Actualiza solo campos<br/>que vienen en Request"]
    end

    subgraph "RESPUESTA"
        J["Si success: true<br/>UsuarioModel.get_by_id<br/>Retorna usuario actualizado"]
    end

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J
```

### 4. GUARDAR/OBTENER DATOS CORPORALES

#### 4.1 POST /usuarios/me/datos-corporales (Primera vez)

```mermaid
graph TD
    subgraph "ENDPOINT: POST /usuarios/me/datos-corporales"
        A["Cliente envía:<br/>{ altura: float, peso: float }"]
        B["UsuarioDateCorporal Model"]
    end

    subgraph "VALIDACION"
        C["Valida token Bearer"]
        D["Extrae user_id del payload"]
    end

    subgraph "MODELO"
        E["UsuarioModel.savedDateCorporal<br/>- user_id<br/>- altura<br/>- peso"]
    end

    subgraph "DATABASE"
        F["INSERT INTO datoscorporales<br/>(usuario_id, altura, peso, fecha_creacion)<br/>VALUES (%s, %s, %s, NOW())"]
        G["TABLA: datoscorporales<br/>- id INT PRIMARY KEY<br/>- usuario_id INT FK<br/>- altura FLOAT<br/>- peso FLOAT<br/>- fecha_creacion TIMESTAMP"]
    end

    subgraph "RESPUESTA"
        H["{ success: true,<br/>  message: Datos guardados }"]
    end

    A --> B --> C --> D --> E --> F --> G --> H
```

#### 4.2 GET /usuarios/me/datos-corporales

```mermaid
graph TD
    A["GET /usuarios/me/datos-corporales<br/>Header: Authorization"] --> B["Valida token"]
    B --> C["Extrae user_id"]
    C --> D["UsuarioModel.get_datecorporal<br/>user_id"]
    D --> E["SELECT * FROM datoscorporales<br/>WHERE usuario_id = %s"]
    E --> F["Retorna datos corporales<br/>altura, peso, fecha_creacion"]
```

#### 4.3 PATCH /usuarios/me/datos-corporales (Actualizar)

```mermaid
graph TD
    A["PATCH /usuarios/me/datos-corporales<br/>Body: UsuarioUpdateDateCorporal<br/>- altura: float | None<br/>- peso: float | None"]
    B["Valida token Bearer"]
    C["Construye diccionario<br/>solo con campos NOT NULL"]
    D["UsuarioModel.updateDateCorporal<br/>- user_id, campos dict"]
    E["UPDATE dinámico<br/>UPDATE datoscorporales SET<br/>altura = %s,<br/>peso = %s<br/>WHERE usuario_id = %s"]
    F["{ success: true,<br/>  message: Actualizado }"]
    
    A --> B --> C --> D --> E --> F
```

### 5. OBJETIVO DE PESO Y METAS NUTRICIONALES

#### 5.1 POST /usuarios/me/objetivo-peso (Calcular metas)

```mermaid
graph TD
    subgraph "ENDPOINT"
        A["POST /usuarios/me/objetivo-peso<br/>Body: ObjetivoPesoRequest<br/>{ objetivo: bajar|subir|mantener|ninguno }"]
    end

    subgraph "PASO 1: VALIDACION"
        B["Valida token Bearer"]
        C["Extrae user_id"]
    end

    subgraph "PASO 2: OBTENER DATOS"
        D["UsuarioModel.get_by_id user_id"]
        E["Obtiene: fecha_nacimiento, sexo"]
        F["UsuarioModel.get_datos_corporales"]
        G["Obtiene: peso, altura"]
    end

    subgraph "PASO 3: CALCULAR"
        H["NutricionService.calcular_edad<br/>fecha_nacimiento → edad"]
        I["NutricionService.calcular_metas<br/>- objetivo<br/>- sexo<br/>- peso<br/>- altura<br/>- edad"]
        J["calcular_tmb(sexo,peso,altura,edad)<br/>Formula Mifflin-St Jeor:<br/>Si Masculino: (10*P)+(6.25*A)-(5*E)+5<br/>Si Femenino: (10*P)+(6.25*A)-(5*E)-161"]
        K["Ajusta según objetivo:<br/>bajar: tmb - 500<br/>subir: tmb + 500<br/>mantener: tmb<br/>ninguno: tmb"]
        L["Calcula macros:<br/>P: 30% calorias/4<br/>G: 25% calorias/9<br/>C: 45% calorias/4<br/>A: 10% carbohidratos"]
    end

    subgraph "PASO 4: GUARDAR"
        M["UsuarioModel.save_objetivo<br/>user_id, objetivo"]
        N["INSERT/UPDATE tabla objetivos"]
        O["UsuarioModel.save_meta_nutricional<br/>user_id, metas dict"]
        P["INSERT/UPDATE tabla metasnutricionales"]
    end

    subgraph "TABLAS"
        Q["TABLA: objetivos<br/>- id<br/>- usuario_id FK<br/>- objetivo_peso<br/>- fecha_creacion"]
        R["TABLA: metasnutricionales<br/>- id<br/>- usuario_id FK<br/>- calorias FLOAT<br/>- proteinas FLOAT<br/>- grasas FLOAT<br/>- carbohidratos FLOAT<br/>- azucares FLOAT"]
    end

    subgraph "RESPUESTA"
        S["{ success: true,<br/>  objetivo: string,<br/>  metas: {<br/>    calorias,<br/>    proteinas,<br/>    grasas,<br/>    carbohidratos,<br/>    azucares<br/>  }<br/>}"]
    end

    A --> B --> C --> D --> E --> F --> G
    G --> H --> I --> J --> K --> L --> M --> N --> O --> P
    N --> Q
    P --> R
    M --> S
    O --> S
```

#### 5.2 GET /usuarios/me/objetivo-peso

```mermaid
graph TD
    A["GET /usuarios/me/objetivo-peso"] --> B["Valida token"]
    B --> C["UsuarioModel.get_objetivo user_id"]
    C --> D["SELECT objetivo_peso FROM objetivos<br/>WHERE usuario_id = %s"]
    D --> E["{ success: true,<br/>  objetivo: string }"]
```

#### 5.3 GET /usuarios/me/meta-nutricional

```mermaid
graph TD
    A["GET /usuarios/me/meta-nutricional"] --> B["Valida token"]
    B --> C["UsuarioModel.get_meta_nutricional user_id"]
    C --> D["SELECT * FROM metasnutricionales<br/>WHERE usuario_id = %s"]
    D --> E["{ success: true,<br/>  metas: { calorias, proteinas,<br/>    grasas, carbohidratos,<br/>    azucares } }"]
```

#### 5.4 POST y PATCH /usuarios/me/meta-nutricional/ninguno

```mermaid
graph TD
    subgraph "POST: Guardar datos personalizados (objetivo=ninguno)"
        A["POST Body: MetaPersonalizada<br/>{ calorias, proteinas,<br/>  grasas, carbohidratos,<br/>  azucares }"]
        B["Valida token"]
        C["Construye metas dict"]
        D["UsuarioModel.patch_meta_nutricional<br/>user_id, metas"]
        E["UPDATE metasnutricionales<br/>SET calorias=%s, proteinas=%s...<br/>WHERE usuario_id=%s"]
    end

    subgraph "POST: Guardar ceros (sin objetivo)"
        F["POST /meta-nutricional/ninguno<br/>Sin body"]
        G["Valida token"]
        H["UsuarioModel.post_no_objetivo<br/>user_id"]
        I["INSERT/UPDATE metasnutricionales<br/>Todos campos = 0.00"]
    end

    A --> B --> C --> D --> E
    F --> G --> H --> I
```

### 6. ENFERMEDADES CORPORALES (SALUD CORPORAL)

```mermaid
graph TD
    subgraph "MODELOS"
        A["EnfermedadItem:<br/>{ nombre: str,<br/>  fecha_padecimiento: str }"]
        B["SaludCorporalRequest:<br/>{ enfermedades: List[EnfermedadItem] }"]
    end

    subgraph "POST /usuarios/me/salud-corporal"
        C["Cliente envía datos de<br/>múltiples enfermedades"]
        D["Valida token"]
        E["Itera cada enfermedad"]
        F["UsuarioModel.add_salud_corporal<br/>user_id, nombre, fecha"]
        G["INSERT INTO saludcorporal<br/>(usuario_id, nombre,<br/>fecha_padecimiento)<br/>VALUES (%s,%s,%s)"]
    end

    subgraph "GET /usuarios/me/salud-corporal"
        H["Valida token"]
        I["UsuarioModel.get_salud_corporal<br/>user_id"]
        J["SELECT * FROM saludcorporal<br/>WHERE usuario_id = %s"]
    end

    subgraph "DELETE /usuarios/me/salud-corporal/{id}"
        K["Valida token"]
        L["UsuarioModel.delete_salud_corporal<br/>user_id, enfermedad_id"]
        M["DELETE FROM saludcorporal<br/>WHERE id=%s AND usuario_id=%s"]
    end

    subgraph "TABLA"
        N["TABLA: saludcorporal<br/>- id INT PRIMARY KEY<br/>- usuario_id INT FK<br/>- nombre VARCHAR<br/>- fecha_padecimiento DATE<br/>- fecha_creacion TIMESTAMP"]
    end

    A --> B --> C --> D --> E --> F --> G
    H --> I --> J
    K --> L --> M
    G -.INSERT.-> N
    J -.SELECT.-> N
    M -.DELETE.-> N
```

### 7. ENFERMEDADES ALIMENTICIAS (SALUD ALIMENTICIA)

```mermaid
graph TD
    subgraph "MODELOS"
        A["EnfermedadAlimenticiaItem:<br/>{ nombre: str }"]
        B["SaludAlimenticiaRequest:<br/>{ enfermedades: List[EnfermedadAlimenticiaItem] }"]
    end

    subgraph "POST /usuarios/me/salud-alimenticia"
        C["Cliente envía lista de<br/>enfermedades alimenticias"]
        D["Valida token"]
        E["Itera cada enfermedad"]
        F["UsuarioModel.add_salud_alimenticia<br/>user_id, nombre"]
        G["INSERT INTO saludalimenticia<br/>(usuario_id, nombre)<br/>VALUES (%s,%s)"]
    end

    subgraph "GET /usuarios/me/salud-alimenticia"
        H["Valida token"]
        I["UsuarioModel.get_salud_alimenticia<br/>user_id"]
        J["SELECT * FROM saludalimenticia<br/>WHERE usuario_id = %s"]
    end

    subgraph "DELETE /usuarios/me/salud-alimenticia/{id}"
        K["Valida token"]
        L["UsuarioModel.delete_salud_alimenticia<br/>user_id, enfermedad_id"]
        M["DELETE FROM saludalimenticia<br/>WHERE id=%s AND usuario_id=%s"]
    end

    subgraph "TABLA"
        N["TABLA: saludalimenticia<br/>- id INT PRIMARY KEY<br/>- usuario_id INT FK<br/>- nombre VARCHAR<br/>- fecha_creacion TIMESTAMP"]
    end

    A --> B --> C --> D --> E --> F --> G
    H --> I --> J
    K --> L --> M
    G -.INSERT.-> N
    J -.SELECT.-> N
    M -.DELETE.-> N
```

## Estructura de Clases y Funciones Explicadas

### ROUTES (Capa de Rutas - Definición de Endpoints)

#### auth.py
- **GoogleTokenRequest**: Modelo Pydantic - Valida que token sea string
- **GoogleLoginResponse**: Modelo Pydantic - Estructura respuesta: status, usuario, mensaje
- **@router.post("/google")**: Endpoint que recibe token Google y ejecuta AuthController.google_login()

#### usuario.py
- **Modelos Pydantic**: Define estructura datos entrada/salida
  - UsuarioUpdateRequest
  - UsuarioDateCorporal
  - UsuarioUpdateDateCorporal
  - EnfermedadItem, SaludCorporalRequest
  - EnfermedadAlimenticiaItem, SaludAlimenticiaRequest
  - ObjetivoPesoRequest, MetaPersonalizada
- **@router.get/post/patch/delete**: Define endpoints que:
  1. Validan token Bearer
  2. Extraen user_id de payload
  3. Llaman funciones de Model
  4. Retornan respuestas JSON

### CONTROLADORES (Capa de Lógica de Negocio)

#### auth_controller.py - AuthController
- **GOOGLE_CLIENT_ID**: Constante - ID de la app en Google Cloud
- **google_login(token_google)**: Async classmethod
  - Verifica token OAuth2 de Google usando `id_token.verify_oauth2_token()`
  - Extrae: email, nombre, google_id, foto_url
  - Llama UsuarioModel para buscar/crear usuario
  - Genera JWT si es exitoso
  - Retorna dict con usuario y token

### MODELOS (Capa de Base de Datos)

#### usuario_model.py - UsuarioModel
Todas las funciones son @staticmethod (no necesitan instancia)

**Crear Usuario:**
- `create_from_google(email, nombre, google_id, foto_url)`: 
  - INSERT INTO usuario table
  - Retorna user_id

**Buscar Usuario:**
- `get_by_email(email)`: Busca usuario por email, retorna dict o None
- `get_by_id(user_id)`: Busca usuario por ID (para traer datos frescos)

**Actualizar Usuario:**
- `update_google_data(user_id, nombre, google_id, foto_url)`: Actualiza con datos Google
- `update(user_id, campos_dict)`: UPDATE genérico con campos dinámicos
- `updateDateCorporal(user_id, campos_dict)`: UPDATE tabla datoscorporales

**Datos Corporales:**
- `savedDateCorporal(user_id, altura, peso)`: INSERT primera vez
- `get_datecorporal(user_id)`: SELECT datos corporales

**Objetivo y Metas:**
- `save_objetivo(user_id, objetivo)`: INSERT/UPDATE objetivo
- `get_objetivo(user_id)`: SELECT objetivo
- `save_meta_nutricional(user_id, metas_dict)`: INSERT/UPDATE meta
- `get_meta_nutricional(user_id)`: SELECT meta
- `post_no_objetivo(user_id)`: INSERT/UPDATE meta con todos 0.00
- `patch_meta_nutricional(user_id, metas_dict)`: UPDATE meta

**Salud Corporal:**
- `add_salud_corporal(user_id, nombre, fecha)`: INSERT enfermedad corporal
- `get_salud_corporal(user_id)`: SELECT todas enfermedades corporales
- `delete_salud_corporal(user_id, enfermedad_id)`: DELETE enfermedad corporal

**Salud Alimenticia:**
- `add_salud_alimenticia(user_id, nombre)`: INSERT enfermedad alimenticia
- `get_salud_alimenticia(user_id)`: SELECT todas enfermedades alimenticias
- `delete_salud_alimenticia(user_id, enfermedad_id)`: DELETE enfermedad alimenticia

### SERVICIOS (Capa de Lógica de Negocio Especial)

#### nutricion_service.py - NutricionService

- `calcular_edad(fecha_nacimiento)`: 
  - Input: fecha_nacimiento (str o date object)
  - Calcula: hoy.year - nacimiento.year (ajustando por mes/día)
  - Output: edad integer

- `calcular_tmb(sexo, peso, altura, edad)`:
  - Formula Mifflin-St Jeor
  - Si Masculino: (10*peso) + (6.25*altura) - (5*edad) + 5
  - Si Femenino: (10*peso) + (6.25*altura) - (5*edad) - 161
  - Output: TMB float

- `calcular_metas(objetivo, sexo, peso, altura, edad)`:
  - Llama calcular_tmb() primero
  - Ajusta calorías según objetivo:
    - "bajar": tmb - 500
    - "subir": tmb + 500
    - "mantener": tmb
  - Calcula macros basado en calorías:
    - Proteinas: 30% de calorias / 4
    - Grasas: 25% de calorias / 9
    - Carbohidratos: 45% de calorias / 4
    - Azúcares: 10% de carbohidratos
  - Output: dict con {calorias, proteinas, grasas, carbohidratos, azucares}

### UTILIDADES (Funciones Auxiliares)

#### config/database.py
- `get_connection()`: 
  - Lee variables entorno (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
  - Crea conexión MySQL
  - Retorna connection object o None si falla

#### utils/generate_jwt.py - GenerateJwt
- **Constantes de clase**:
  - SECRET_KEY: de .env JWT_SECRET_KEY
  - ALGORITHM: de .env ALGORITHM (típicamente HS256)
  - ACCESS_TOKEN_EXPIRE_MINUTES: 60 * 24 * 7 = 10080 min = 7 días

- `create_jwt(user_id, email)`: Async classmethod
  - Crea expiracion: datetime.now + timedelta(10080 min)
  - Encripta payload {user_id, email, exp} con JWT
  - Retorna {success: bool, access_token: string} o {success: false, error: string}

#### utils/security.py - VerifyExpiredToken
- **Constantes**: SECRET_KEY, ALGORITHM (mismo que generación)

- `verify_token(token)`: Classmethod
  - jwt.decode() desencripta el token
  - Valida firma digital
  - Extrae email del payload
  - Llama UsuarioModel.get_by_email() para obtener datos frescos
  - Retorna:
    - Si válido: {expired: false, access_token, data: {usuario_data}}
    - Si expirado: {expired: true, access_token}
    - Si inválido: {error: "Token invalido"}

## Flujo de Autenticación por Endpoint

```
TODAS LAS RUTAS PROTEGIDAS:
┌─────────────────────────────────────────────┐
│ 1. Cliente envía request                    │
│    Header: "Authorization": "Bearer xxxxx"  │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ 2. Route Handler en usuario.py              │
│    if not authorization.startswith("Bearer")│
│       → raise HTTPException(401)            │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ 3. Extrae token                             │
│    token = authorization.replace("Bearer ") │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ 4. Verifica Token                           │
│    payload = VerifyExpiredToken.verify_token│
└──────────┬──────────────────────────────────┘
           │
           ├─→ "error" in payload → 401
           ├─→ payload["expired"] → 401
           │
           ▼
┌─────────────────────────────────────────────┐
│ 5. Extrae user_id                           │
│    user_id = payload["data"]["id"]          │
│    Datos usuario en payload["data"]         │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ 6. Ejecuta lógica del endpoint              │
│    Con user_id validado                     │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ 7. Retorna respuesta                        │
└─────────────────────────────────────────────┘
```

## Esquema de Base de Datos

```
TABLA: usuario
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ email (VARCHAR, UNIQUE)
├─ nombre (VARCHAR)
├─ apellido (VARCHAR)
├─ sexo (VARCHAR: "Masculino"/"Femenino")
├─ fecha_nacimiento (DATE)
├─ num_telefono (VARCHAR)
├─ google_id (VARCHAR)
├─ foto_url (VARCHAR)
└─ activo (BOOLEAN)

TABLA: datoscorporales
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ usuario_id (INT, FOREIGN KEY → usuario.id)
├─ altura (FLOAT: centímetros)
├─ peso (FLOAT: kilogramos)
└─ fecha_creacion (TIMESTAMP)

TABLA: objetivos
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ usuario_id (INT, FOREIGN KEY → usuario.id, UNIQUE)
├─ objetivo_peso (VARCHAR: "bajar"/"subir"/"mantener"/"ninguno")
└─ fecha_creacion (TIMESTAMP)

TABLA: metasnutricionales
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ usuario_id (INT, FOREIGN KEY → usuario.id, UNIQUE)
├─ calorias (FLOAT)
├─ proteinas (FLOAT)
├─ grasas (FLOAT)
├─ carbohidratos (FLOAT)
├─ azucares (FLOAT)
└─ fecha_actualizacion (TIMESTAMP)

TABLA: saludcorporal
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ usuario_id (INT, FOREIGN KEY → usuario.id)
├─ nombre (VARCHAR: enfermedad/condición)
├─ fecha_padecimiento (DATE)
└─ fecha_creacion (TIMESTAMP)

TABLA: saludalimenticia
├─ id (INT, PRIMARY KEY, AUTO_INCREMENT)
├─ usuario_id (INT, FOREIGN KEY → usuario.id)
├─ nombre (VARCHAR: enfermedad/alergia)
└─ fecha_creacion (TIMESTAMP)
```

## Flujo Completo de Ejemplo: Usuario Nueva Registración

```
1. FRONTEND envía token Google a POST /auth/google

2. auth.py valida estructura con GoogleTokenRequest Pydantic

3. auth_controller.py:
   - Verifica token con Google servers (id_token.verify_oauth2_token)
   - Extrae: email, nombre, google_id, foto_url
   
4. usuario_model.py:
   - get_by_email(email) → No existe
   - create_from_google(email, nombre, google_id, foto_url)
   - INSERT INTO usuario table
   - Retorna user_id

5. generate_jwt.py:
   - create_jwt(user_id, email)
   - Encripta JWT con exp=7 días
   - Retorna access_token

6. Respuesta al cliente:
   {
     "success": true,
     "usuario": {
       "id": 1,
       "email": "user@example.com",
       "nombre": "Juan",
       "foto_url": "https://...",
       "tokenjwt": "eyJ0eXAi...",
       "nuevo": true
     }
   }

7. Cliente guarda token y lo usa en futuros requests

8. Cliente POST /usuarios/me/datos-corporales:
   - Envía: { "altura": 175, "peso": 70 }
   - Header: "Authorization": "Bearer eyJ0eXAi..."
   
9. usuario.py valida token → extrae user_id
   
10. usuario_model.savedDateCorporal(user_id, 175, 70)
    - INSERT INTO datoscorporales
    
11. Cliente POST /usuarios/me/objetivo-peso:
    - Envía: { "objetivo": "bajar" }
    
12. usuario.py valida token → extrae user_id

13. Calcula:
    - get_by_id → obtiene sexo, fecha_nacimiento
    - get_datos_corporales → obtiene peso, altura
    - calcular_edad(fecha_nacimiento) → edad
    - calcular_metas("bajar", sexo, peso, altura, edad)
      - calcular_tmb(sexo, peso, altura, edad)
      - Ajusta: tmb - 500
      - Calcula macros
      
14. usuario_model:
    - save_objetivo(user_id, "bajar")
    - save_meta_nutricional(user_id, metas_dict)
    - INSERT en ambas tablas
    
15. Respuesta:
    {
      "success": true,
      "objetivo": "bajar",
      "metas": {
        "calorias": 2000,
        "proteinas": 150,
        "grasas": 82,
        "carbohidratos": 245,
        "azucares": 24.5
      }
    }
```

## Resumen de Dependencias

```
main.py
├── FastAPI framework
├── CORSMiddleware
├── routes.auth
│   └── controllers.auth_controller
│       ├── models.usuario_model
│       │   └── config.database (MySQL connection)
│       └── utils.generate_jwt
│           └── jose (JWT library)
└── routes.usuario
    ├── utils.security (VerifyExpiredToken)
    │   ├── jose (JWT decode)
    │   └── models.usuario_model
    ├── models.usuario_model
    │   └── config.database
    ├── services.nutricion_service
    └── pydantic (data validation)
```

## Variables de Entorno Requeridas (.env)

```
# DATABASE
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=nutriescan

# JWT
JWT_SECRET_KEY=tu_clave_secreta_muy_larga
ALGORITHM=HS256

# GOOGLE AUTH
GOOGLE_CLIENT_ID=tu_client_id_de_google.apps.googleusercontent.com
```

## Resumen de Endpoints

| Método | Ruta | Función | Requiere Auth |
|--------|------|---------|---------------|
| POST | /auth/google | Autenticar con Google | No |
| GET | / | Root endpoint | No |
| GET | /health | Health check DB | No |
| GET | /usuarios/me | Verificar JWT y obtener datos | Sí |
| PATCH | /usuarios/me | Actualizar perfil usuario | Sí |
| POST | /usuarios/me/datos-corporales | Guardar altura/peso | Sí |
| GET | /usuarios/me/datos-corporales | Obtener datos corporales | Sí |
| PATCH | /usuarios/me/datos-corporales | Actualizar datos corporales | Sí |
| POST | /usuarios/me/objetivo-peso | Guardar objetivo y calcular metas | Sí |
| GET | /usuarios/me/objetivo-peso | Obtener objetivo | Sí |
| POST | /usuarios/me/meta-nutricional/ninguno | Guardar datos cero | Sí |
| PATCH | /usuarios/me/meta-nutricional/ninguno | Actualizar datos personalizados | Sí |
| GET | /usuarios/me/meta-nutricional | Obtener metas nutricionales | Sí |
| POST | /usuarios/me/salud-corporal | Guardar enfermedades corporales | Sí |
| GET | /usuarios/me/salud-corporal | Obtener enfermedades corporales | Sí |
| DELETE | /usuarios/me/salud-corporal/{id} | Eliminar enfermedad corporal | Sí |
| POST | /usuarios/me/salud-alimenticia | Guardar restricciones alimenticias | Sí |
| GET | /usuarios/me/salud-alimenticia | Obtener restricciones alimenticias | Sí |
| DELETE | /usuarios/me/salud-alimenticia/{id} | Eliminar restricción alimenticia | Sí |
