from PyPDF2 import PdfReader
from datetime import date, datetime
import base64
import os
from typing import Any

def get_pdf_chunks(path: str) -> list[str]:
    """Divide el PDF en una lista de textos, uno por página. (Sin cambios)"""
    print(f"📄 Dividiendo el PDF: {os.path.basename(path)}...")
    reader = PdfReader(path)
    if not reader.pages:
        raise ValueError("El PDF está vacío o no se puede leer.")
    
    chunks = [page.extract_text().strip() for page in reader.pages if page.extract_text() and page.extract_text().strip()]
    print(f"   PDF dividido en {len(chunks)} páginas (chunks).")
    return chunks

def _serialize_special_types(obj):
    """Función recursiva para convertir fechas a ISO y bytes a Base64."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode('utf-8')
    if isinstance(obj, dict):
        return {k: _serialize_special_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_special_types(i) for i in obj]
    return obj


def sanitize_for_logging(data: Any) -> Any:
    """
    Sanea de forma recursiva un diccionario o lista para el logging.
    Trunca las cadenas largas (especialmente las que parecen base64) para evitar saturar los logs.
    """
    if isinstance(data, dict):
        return {k: sanitize_for_logging(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_for_logging(i) for i in data]
    if isinstance(data, str) and len(data) > 256:  # Truncar cadenas largas
        return f"{data[:80]}... (truncado) ...{data[-80:]}"
    return data
