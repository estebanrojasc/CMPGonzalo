# Ejemplo conceptual de clasificador con instructor
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any  
from PyPDF2 import PdfReader
from datetime import date
from app.extractGraph import extraer_graficos_mysteel
import os

# Parchear el cliente de OpenAI con instructor
client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

class PrecioConFecha(BaseModel):
    valor: float
    fecha: date

class DatosPlatts(BaseModel):
    precio_62_cfr_china: Optional[PrecioConFecha] = None
    precio_65_cfr_china: Optional[PrecioConFecha] = None
    precio_IOMGD00: Optional[PrecioConFecha] = None

class DatosFastmarkets(BaseModel):
    mb_iro_0009: Optional[PrecioConFecha] = None  # Iron ore 65% Fe Brazil-origin
    mb_iro_0019_viu: Optional[PrecioConFecha] = None  # Iron ore 65% Fe VIU

class DatosBaltic(BaseModel):
    c3_tubarao_qingdao: Optional[PrecioConFecha] = None

class DatosInventarioMysteel(BaseModel):
    pellet: PrecioConFecha
    concentrate: PrecioConFecha
    lump: PrecioConFecha
    fines: PrecioConFecha
    australian_iron_ore: PrecioConFecha
    brazilian_iron_ore: PrecioConFecha

class ResumenNoticia(BaseModel):
    titulo: str
    resumen: str
    sentimiento: str = Field(..., description="El sentimiento de la noticia: Positivo, Negativo o Neutral.")

class NoticiasMysteel(BaseModel):
    noticias: List[ResumenNoticia]

def extraer_platts(texto: str) -> DatosPlatts:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=DatosPlatts,
        messages=[
            {"role": "system", "content": """Eres un experto en extracción de precios de reportes financieros. Extrae los siguientes precios desde el texto, asegurándote de identificar la **fecha exacta asociada a cada uno**:

- Platts 62% CFR China
- Platts 65% CFR China
- Platts IOMGD00

**Si un precio no está presente o no puede ser identificado con claridad, omítelo y no lo inventes.**
Devuelve solo los campos que estén presentes en el texto con su respectiva fecha."""},
            {"role": "user", "content": texto}
        ]
    )

def extraer_fastmarkets(texto: str) -> DatosFastmarkets:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=DatosFastmarkets,
        messages=[
            {"role": "system", "content": """Eres un experto en extracción de precios de reportes financieros. Extrae los siguientes precios desde el texto, asegurándote de identificar la **fecha exacta asociada a cada uno**:

- FastMarkets MB-IRO-0009
- FastMarkets MB-IRO-0019 VIU

**Si un precio no está presente o no puede ser identificado con claridad, omítelo y no lo inventes.**
Devuelve solo los campos que estén presentes en el texto con su respectiva fecha."""},
            {"role": "user", "content": texto}
        ]
    )

def extraer_baltic(texto: str) -> DatosBaltic:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=DatosBaltic,
        messages=[
            {"role": "system", "content": """Eres un experto en extracción de precios de reportes financieros. Extrae el precio de C3 Tubarao to Qingdao **Si un precio no está presente o no puede ser identificado con claridad, omítelo y no lo inventes.**
Devuelve solo los campos que estén presentes en el texto con su respectiva fecha."""},
            {"role": "user", "content": texto}
        ]
    )

def extraer_inventario_mysteel(texto: str) -> DatosInventarioMysteel:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=DatosInventarioMysteel,
        messages=[
            {"role": "system", "content": "Eres un experto en extraer datos de tablas de inventarios. Encuentra todos los valores de las columnas 'Pellet', 'Concentrate', 'Lump', 'Fines', 'Australian Iron Ore' y 'Brazilian Iron Ore' y la fecha del reporte desde el texto."},
            {"role": "user", "content": texto}
        ]
    )

def extraer_noticias_mysteel(texto: str) -> NoticiasMysteel:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=NoticiasMysteel,
        messages=[
            {"role": "system", "content": "Eres un analista experto. Identifica las noticias más importantes del texto, extrae su titular, un breve resumen y su sentimiento de mercado."},
            {"role": "user", "content": texto}
        ]
    )


# Diccionario para llamar a la función correcta dinámicamente
EXTRACTORS = {
    "Platts": extraer_platts,
    "FastMarkets": extraer_fastmarkets,
    "Baltic": extraer_baltic,
    # Añadimos las nuevas funciones específicas para tareas
    "extraer_inventario_mysteel": extraer_inventario_mysteel,
    "extraer_noticias_mysteel": extraer_noticias_mysteel,
    "extraer_graficos_mysteel": extraer_graficos_mysteel
}