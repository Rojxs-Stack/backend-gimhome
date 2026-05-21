import os
from openai import OpenAI
import base64

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class VisionService:
    @staticmethod
    def analizar_imagen(image_bytes):
        """
        Analiza una imagen de comida y devuelve valores nutricionales en formato TOON.
        
        TOON (Token-Oriented Object Notation) es un formato compacto diseñado para
        reducir el uso de tokens en respuestas de LLMs, logrando 30-60% de ahorro
        comparado con JSON [citation:6][citation:7].
        
        Args:
            image_bytes: Bytes de la imagen (ya optimizada)
            
        Returns:
            str: Respuesta en formato TOON o dict con error
        """
        try:
            # Codificar a base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Prompt optimizado para TOON
            # TOON usa sintaxis: clave[longitud]{campos}: valor1,valor2,... [citation:1][citation:6]
            prompt = """Eres un nutricionista experto analizando imágenes de comidas por visión artificial.

                        Analiza TODOS los elementos comestibles y bebibles visibles en la imagen completa (plato principal, guarniciones, pan, vasos, tazas, postres, salsas, cubiertos con restos, etc.). No ignores ningún alimento o bebida que aparezca en el encuadre, por pequeño que sea.
                        
                        IMPORTANTE - SI NO HAY COMIDA NI BEBIDA VISIBLE:
                        Si la imagen NO contiene ningún alimento o bebida identificable (ej: es una persona, un paisaje, un objeto no comestible, una mascota, una foto borrosa de algo no identificable como comida), debes responder EXACTAMENTE:
                        datos[1]{nombre,calorias,proteinas,grasas,carbohidratos,azucares}: "NO_COMIDA",-1.0,-1.0,-1.0,-1.0,-1.0
                        
                        SI SÍ HAY COMIDA O BEBIDA:
                        PRIMERO: Crea un nombre descriptivo breve que resuma el conjunto completo (ej: "Pollo asado con puré, pan y jugo de naranja").
                        SEGUNDO: Calcula la suma nutricional TOTAL de absolutamente todos los elementos identificados.
                        
                        Responde EXCLUSIVAMENTE con esta línea de texto en formato TOON. Nada de markdown, ni frases, ni explicaciones:
                        datos[1]{nombre,calorias,proteinas,grasas,carbohidratos,azucares}: "nombre_string",num,num,num,num,num
                        
                        Reglas de análisis:
                        - ELEMENTOS: Considera TODO lo visible. Si hay un vaso, estima su contenido. Si hay un pan, súmalo.
                        - BEBIDAS: Vaso transparente oscuro -> "Coca-Cola" (~140 cal/vaso). Líquido naranja -> "Jugo de naranja" (~120 cal). Agua -> 0 cal.
                        - PAN: Un pan francés estándar visible -> ~140 cal, 5g prot, 1g grasa, 28g carb.
                        - NOMBRE: Máximo 60 caracteres. DEBE ir entre comillas dobles. Enumera los componentes principales visibles.
                        - CONSERVADOR: Ante duda del ingrediente, asume versión estándar (no diet/light).
                        - DECIMALES: Punto decimal. Máximo 1 decimal.
                        - FORMATO ESTRICTO: Solo la línea TOON. Nada antes, nada después.
                        
                        Ejemplo 1 (Plato único):
                        datos[1]{nombre,calorias,proteinas,grasas,carbohidratos,azucares}: "Pollo con arroz y brócoli",550.0,35.5,18.0,60.0,2.0
                        
                        Ejemplo 2 (Bandeja con pan y bebida):
                        datos[1]{nombre,calorias,proteinas,grasas,carbohidratos,azucares}: "Lomo con papas+ensalada+pan+Coca-Cola",920.5,45.0,32.0,105.0,38.0
                        """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,      # Suficiente para la respuesta TOON
                temperature=0        # Consistencia máxima en el formato
            )
            print(response.choices[0].message.content)
            return response.choices[0].message.content

        except Exception as e:
            return {"error": str(e)}