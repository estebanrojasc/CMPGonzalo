import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import os
from typing import Dict, Any

def extraer_graficos_mysteel(pdf_path: str) -> Dict[str, Any]:
    """
    Extrae gráficos de reportes Mysteel basándose en títulos específicos.
    """
    dpi = 300
    
    titles = [
        "Capacity utilization BF & EAF (%)",
        "Domestic Iron Ore Mines Operation",
        "Weekly Imported Iron Ore Volume (10,000t)",
        "Ports & Steel Mills Inventories (10,000t)",
        "Blast Furnace Iron Ore Burden Ratio (%)",
        "Coke Inventory & Capacity Utilization"
    ]

    doc = fitz.open(pdf_path)
    
    title_positions = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        for title in titles:
            found = page.search_for(title)
            if found:
                y = found[0].y0
                title_positions.append({
                    "title": title,
                    "page": page_num,
                    "y": y
                })

    title_positions = sorted(title_positions, key=lambda x: (x["page"], x["y"]))
    
    output_dir = "output_bloques"
    os.makedirs(output_dir, exist_ok=True)
    
    graficos_extraidos = []
    
    for i in range(len(title_positions)):
        title_i = title_positions[i]
        page_i = title_i["page"]
        y_start_pt = title_i["y"]
        
        if i + 1 < len(title_positions):
            title_next = title_positions[i + 1]
            page_next = title_next["page"]
            y_end_pt = title_next["y"]
        else:
            page_next = page_i
            y_end_pt = doc[page_i].rect.height

        pix = doc[page_i].get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        width, height = img.size

        y_start_px = int(y_start_pt * dpi / 72)
        y_end_px = int(y_end_pt * dpi / 72) if page_i == page_next else height

        cropped = img.crop((0, y_start_px, width, y_end_px))

        # Guardar localmente
        short_title = title_i["title"][:30].replace(" ", "_").replace("/", "")
        filename = f"{i+1}_p{page_i+1}_{short_title}.png"
        output_path = os.path.join(output_dir, filename)
        cropped.save(output_path)

        # Agregar información del gráfico
        grafico_info = {
            "numero": i + 1,
            "titulo": title_i["title"],
            "pagina": page_i + 1,
            "archivo_png": output_path,
            "altura_px": y_end_px - y_start_px
        }
        graficos_extraidos.append(grafico_info)

    doc.close()
    
    return {
        "total_graficos": len(graficos_extraidos),
        "graficos": graficos_extraidos
    }

# # Para pruebas directas
# if __name__ == "__main__":
#     pdf_path = r"D:\Esteban\GerenciaComercial\Documentos Marketing\MySteel\Mysteel Raw Materials Daily 20241128.pdf"
#     resultado = extraer_graficos_mysteel(pdf_path)
#     print(f"Se extrajeron {resultado['total_graficos']} gráficos")
#     print(resultado)