
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from app.config.settings import *

client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

class PrecioConFecha(BaseModel):
    valor: float = Field(..., description="El valor numérico del precio/inventario.")
    fecha: Optional[date] = Field(None, description="La fecha asociada al valor, si está disponible.")

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
    pellet: Optional[PrecioConFecha] = None
    concentrate: Optional[PrecioConFecha] = None
    lump: Optional[PrecioConFecha] = None
    fines: Optional[PrecioConFecha] = None
    australian_iron_ore: Optional[PrecioConFecha] = None
    brazilian_iron_ore: Optional[PrecioConFecha] = None

class ResumenNoticia(BaseModel):
    """Representa una única noticia extraída de un documento."""
    titulo: str = Field(..., description="El titular principal de la noticia.")
    resumen: str = Field(..., description="Un resumen conciso de la noticia en 2-3 frases.")
    sentimiento: str = Field(..., description="El sentimiento de mercado (Positivo, Negativo, Neutral).")
    fecha_noticia: Optional[date] = Field(None, description="La fecha de publicación de la noticia, si se encuentra.")

class NoticiasMysteel(BaseModel):
    """Una lista de todas las noticias importantes encontradas en el documento."""
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
            {"role": "system", "content": "Eres un analista experto. Identifica las noticias más importantes del texto, extrae su titular, un breve resumen, su sentimiento de mercado y la fecha de la noticia si está disponible."},
            {"role": "user", "content": texto}
        ]
    )

EXTRACTORS = {
    "Platts": extraer_platts,
    "FastMarkets": extraer_fastmarkets,
    "Baltic": extraer_baltic,
    # Añadimos las nuevas funciones específicas para tareas
    "extraer_inventario_mysteel": extraer_inventario_mysteel,
    "extraer_noticias_mysteel": extraer_noticias_mysteel
}