from datetime import date

class NutricionService:
    
    @staticmethod
    def calcular_edad(fecha_nacimiento):
        """Calcula edad a partir de fecha de nacimiento"""
        if isinstance(fecha_nacimiento, str):
            fecha_nacimiento = date.fromisoformat(fecha_nacimiento)
        hoy = date.today()
        return hoy.year - fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )
    
    @staticmethod
    def calcular_tmb(sexo: str, peso, altura, edad: int):
        """Calcula Tasa Metabólica Basal (TMB) con Mifflin-St Jeor"""
        # Convertir Decimal a float si es necesario
        peso_float = float(peso) if hasattr(peso, '__float__') else peso
        altura_float = float(altura) if hasattr(altura, '__float__') else altura
        
        if sexo == "Masculino":
            return (10 * peso_float) + (6.25 * altura_float) - (5 * edad) + 5
        else:  # Femenino
            return (10 * peso_float) + (6.25 * altura_float) - (5 * edad) - 161
    
    @staticmethod
    def calcular_metas(objetivo: str, sexo: str, peso, altura, edad: int):
        """Calcula metas nutricionales según objetivo"""
        tmb = NutricionService.calcular_tmb(sexo, peso, altura, edad)
        
        # Ajuste según objetivo
        if objetivo == "bajar":
            calorias = tmb - 500  # Déficit calórico
        elif objetivo == "subir":
            calorias = tmb + 500  # Superávit calórico
        elif objetivo == "mantener":
            calorias = tmb
        else:
            calorias = tmb
        
        # Macros (valores aproximados)
        proteinas = (calorias * 0.30) / 4  # 30% de proteínas (4 kcal/g)
        grasas = (calorias * 0.25) / 9     # 25% de grasas (9 kcal/g)
        carbohidratos = (calorias * 0.45) / 4  # 45% de carbohidratos (4 kcal/g)
        azucares = carbohidratos * 0.10    # 10% de carbohidratos como azúcares
        
        return {
            "calorias": round(calorias, 2),
            "proteinas": round(proteinas, 2),
            "grasas": round(grasas, 2),
            "carbohidratos": round(carbohidratos, 2),
            "azucares": round(azucares, 2)
        }