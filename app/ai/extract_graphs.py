import fitz  # PyMuPDF
import base64
from typing import Dict, Any, List
from datetime import date

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional

from app.config.settings import *

client = instructor.patch(OpenAI(api_key=OPENAI_API_KEY))

class GraficoAnalizado(BaseModel):
    """Representa el análisis de un único gráfico."""
    titulo: str = Field(..., description="Un título claro y conciso que resuma el gráfico. Ej: 'Utilización de Capacidad de Altos Hornos (BF) y Hornos de Arco Eléctrico (EAF)'.")
    descripcion_ia: str = Field(..., description="Una descripción detallada de los datos que muestra el gráfico, incluyendo tendencias, cifras clave y unidades. Ej: 'La utilización de BF disminuyó al 85%, mientras que la de EAF aumentó al 60% en la última semana.'")
    fecha_grafico: Optional[date] = Field(None, description="La fecha a la que se refieren los datos del gráfico, si se puede inferir del contenido.")

class AnalisisDeGraficos(BaseModel):
    """Una lista con el análisis de todos los gráficos proporcionados."""
    graficos: List[GraficoAnalizado]


def extraer_graficos_mysteel(pdf_path: str) -> Dict[str, Any]:
    """
    Extrae imágenes de gráficos de un PDF, las analiza con IA, y devuelve los datos enriquecidos.
    """
    print("--- 🔍 Iniciando extracción de gráficos con PyMuPDF ---")
    
    imagenes_extraidas = []
    try:
        doc = fitz.open(pdf_path)
        
        titles = [
            "Capacity utilization BF & EAF (%)", "Domestic Iron Ore Mines Operation",
            "Weekly Imported Iron Ore Volume (10,000t)", "Ports & Steel Mills Inventories (10,000t)",
            "Blast Furnace Iron Ore Burden Ratio (%)", "Coke Inventory & Capacity Utilization"
        ]
        
        title_positions = []
        for page_num, page in enumerate(doc):
            for title in titles:
                found = page.search_for(title)
                if found:
                    title_positions.append({"title": title, "page": page_num, "y": found[0].y0})

        title_positions = sorted(title_positions, key=lambda x: (x["page"], x["y"]))

        for i, current_title in enumerate(title_positions):
            page = doc[current_title["page"]]
            y0 = current_title["y"]
            y1 = next((t["y"] for t in title_positions[i+1:] if t["page"] == current_title["page"]), page.rect.height)
            
            clip_area = fitz.Rect(0, y0 - 10, page.rect.width, y1 - 10)
            pix = page.get_pixmap(clip=clip_area, dpi=200)
            
            imagenes_extraidas.append({
                "pagina": current_title["page"] + 1,
                "contenido": pix.tobytes("png")
            })
        
        doc.close()
    except Exception as e:
        print(f"❌ Error durante la extracción de imágenes con PyMuPDF: {e}")
        return {"graficos": []}

    if not imagenes_extraidas:
        print("⚠️ No se encontraron gráficos basados en los títulos.")
        return {"graficos": []}

    print(f"🖼️  Extraídas {len(imagenes_extraidas)} imágenes de gráficos. Enviando a IA para análisis...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=AnalisisDeGraficos,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analista experto en mercados de materias primas. Analiza cada una de las siguientes imágenes de gráficos y extrae la información solicitada en el formato JSON requerido. Sé preciso y conciso.",
                },
                {
                    "role": "user",
                    "content": [
                        "Analiza las siguientes imágenes de gráficos:",
                        *[
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(img['contenido']).decode()}"}}
                            for img in imagenes_extraidas
                        ]
                    ],
                },
            ],
        )
    except Exception as e:
        print(f"❌ Error llamando a la API de OpenAI para analizar gráficos: {e}")
        return {"graficos": []}
        
    print("✅ Análisis de la IA completado.")

    resultados_finales = []
    for i, grafico_analizado in enumerate(response.graficos):
        if i < len(imagenes_extraidas):
            resultado = grafico_analizado.model_dump()
            resultado["pagina"] = imagenes_extraidas[i]["pagina"]
            resultado["contenido"] = imagenes_extraidas[i]["contenido"]
            resultados_finales.append(resultado)
            
    return {"graficos": resultados_finales}
