
from PyPDF2 import PdfReader

def extract_first_page_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    
    if not reader.pages:
        raise ValueError("El PDF no contiene páginas.")
    
    first_page = reader.pages[0]
    text = first_page.extract_text()
    
    if not text:
        raise ValueError("No se pudo extraer texto de la primera página.")
    
    return text.strip()