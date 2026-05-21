import os
from openai import OpenAI
import base64

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class RecetasService:
    @staticmethod
    def generar_receta(image_bytes, calorias_objetivo):
        try:
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            prompt = f"""Eres un chef nutricionista. Analiza la imagen de ingredientes y crea una receta.

                        INGREDIENTES DISPONIBLES (solo usa lo visible en la foto).
                        
                        IMPORTANTE - SI NO HAY COMIDA NI BEBIDA VISIBLE:
                        Si la imagen NO contiene ningún alimento o bebida identificable (ej: es una persona, un paisaje, un objeto no comestible, una mascota, una foto borrosa de algo no identificable como comida), debes responder EXACTAMENTE:
                        datos[1]{{nombre_receta,calorias_totales,proteinas_totales,grasas_totales,carbohidratos_totales,ingredientes_usados,instrucciones,objetivo_alcanzado,maximo_alcanzable}}: "NO_ALIMENTOS",-1.0,-1.0,-1.0,-1.0,-1.0,-1.0,-1.0,-1.0

                        OBJETIVO: {calorias_objetivo} calorías

                        REGLAS ESTRICTAS:
                        1. USA SOLO los ingredientes visibles en la foto.
                        2. Intenta acercarte lo más posible a {calorias_objetivo} calorías.
                        3. Si NO puedes alcanzar ese número, sé HONESTO y devuelve el MÁXIMO alcanzable.
                        4. Prioriza que la receta sea RICA y COHERENTE.

                        FORMATO DE RESPUESTA (TOON):
                        datos[1]{{nombre_receta,calorias_totales,proteinas_totales,grasas_totales,carbohidratos_totales,ingredientes_usados,instrucciones,objetivo_alcanzado,maximo_alcanzable}}: <nombre>,<num>,<num>,<num>,<num>,<ingredientes_json>,<instrucciones_texto>,<bool>,<num>

                        EJEMPLO (Objetivo alcanzado):
                        datos[1]{{nombre_receta,calorias_totales,proteinas_totales,grasas_totales,carbohidratos_totales,ingredientes_usados,instrucciones,objetivo_alcanzado,maximo_alcanzable}}: Pollo con tomate y arroz,430.0,28.5,12.0,52.0,"[{{""nombre"":""pechuga"",""cantidad"":""150g""}},{{""nombre"":""tomate"",""cantidad"":""1 unidad""}},{{""nombre"":""arroz"",""cantidad"":""60g""}}]","1. Cocinar arroz. 2. Saltear pollo con tomate. 3. Servir.",true,430.0

                        EJEMPLO (Objetivo NO alcanzado):
                        datos[1]{{nombre_receta,calorias_totales,proteinas_totales,grasas_totales,carbohidratos_totales,ingredientes_usados,instrucciones,objetivo_alcanzado,maximo_alcanzable}}: Ensalada de pollo y tomate,280.0,25.0,8.0,12.0,"[{{""nombre"":""pechuga"",""cantidad"":""120g""}},{{""nombre"":""tomate"",""cantidad"":""1 unidad""}}]","1. Cocinar pollo. 2. Cortar tomate. 3. Mezclar.",false,280.0
                    """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3  # Un poco de creatividad para recetas
            )
            print(response.choices[0].message.content)
            return response.choices[0].message.content
            
        except Exception as e:
            return {"error": str(e)}