# Ejemplo conceptual de clasificador con instructor
import instructor
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
from datetime import date

from app.config.settings import *

client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

class DocumentSource(BaseModel):
    source: Literal["Mysteel", "FastMarkets", "Platts", "Baltic", "Other"]
    date: date

def classify_with_ai(text_from_first_page: str) -> DocumentSource:
    """
    Clasifica el texto usando gpt-4o-mini con few-shot-prompting y salida estructurada.
    """
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=DocumentSource,
        messages=[
            {"role": "system", "content": "Eres un asistente experto en clasificar reportes. Identifica la fuente y fecha del siguiente texto y responde usando la herramienta proporcionada."},
            {"role": "user", "content": f"Clasifica el siguiente texto: {text_from_first_page}"}
        ]
    )



# # Uso PRIMER PARTE
# first_page_text = extract_first_page_text("app\Fastmarkets Steel raw materials prices & news Daily 2024-11-28.pdf")
# classification = classify_with_ai(first_page_text)
# print(classification.source)
# print(classification.date)

# # Uso PRIMER segunda parte
# from extracData import extraer_por_documento
# from datetime import date

# documento = DocumentSource(source=classification.source, date=classification.date)
# texto_pdf = first_page_text

# resultado = extraer_por_documento(documento, texto_pdf)
# print(resultado)