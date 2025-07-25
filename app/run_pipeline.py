import os
import json
from PyPDF2 import PdfReader
from datetime import date

# 1. Importaciones actualizadas
from app.classifyInit import classify_with_ai, DocumentSource
from app.extracData import EXTRACTORS
from app.vector_db import QdrantManager  # Reemplaza a ChromaDB
import hashlib

# 2. Inicialización del gestor de Qdrant
# Se crea una única instancia que se reutilizará.
qdrant_manager = QdrantManager()

# --- FUNCIONES AUXILIARES ---

def get_pdf_chunks(path: str) -> list[str]:
    """Divide el PDF en una lista de textos, uno por página. (Sin cambios)"""
    print(f"📄 Dividiendo el PDF: {os.path.basename(path)}...")
    reader = PdfReader(path)
    if not reader.pages:
        raise ValueError("El PDF está vacío o no se puede leer.")
    
    chunks = [page.extract_text().strip() for page in reader.pages if page.extract_text() and page.extract_text().strip()]
    print(f"   PDF dividido en {len(chunks)} páginas (chunks).")
    return chunks

# --- PIPELINE PRINCIPAL DE EJECUCIÓN ---

# El registro de tareas no cambia
TASK_REGISTRY = {
    "get_mysteel_inventory": {
        "source": "Mysteel",
        "search_queries": [
            "Tabla con inventarios de mineral de hierro", "Iron Ore Inventories",
            "Pellet inventory", "Concentrate inventory", "Lump inventory",
            "Fines inventory", "Australian iron ore inventory", "Brazilian iron ore inventory"
        ],
        "extractor_func": EXTRACTORS["extraer_inventario_mysteel"]
    },
    "get_mysteel_news": {
        "source": "Mysteel",
        "search_queries": ["Mysteel commentary", "market news", "noticias del mercado de acero"],
        "extractor_func": EXTRACTORS["extraer_noticias_mysteel"]
    },
    "get_platts_prices": {
        "source": "Platts",
        "search_queries": ["Tabla o texto con los precios de Iron Ore Platts 62% y 65% CFR China con su fecha", "Tabla o texto con los precios de IOMGD00 con su fecha"],
        "extractor_func": EXTRACTORS["Platts"]
    },
    "get_fastmarkets_prices": {
        "source": "FastMarkets",
        "search_queries": ["Tabla o texto con los precios de Iron Ore MB-IRO-0009 y MB-IRO-0019 VIU con su fecha de publicación"],
        "extractor_func": EXTRACTORS["FastMarkets"]
    },
    "get_baltic_prices": {
        "source": "Baltic",
        "search_queries": ["Tabla o texto con el precio del flete C3 Tubarao to Qingdao con su fecha"],
        "extractor_func": EXTRACTORS["Baltic"]
    },
    "get_mysteel_graphs": {
        "source": "Mysteel",
        "search_queries": [],
        "extractor_func": EXTRACTORS["extraer_graficos_mysteel"],
        "needs_pdf_path": True
    },
}

# 3. La función `run_task` ahora usa Qdrant para buscar
def run_task(document_info: DocumentSource, task_name: str, pdf_path: str = None):
    """Ejecuta una tarea individual usando Qdrant para la búsqueda semántica."""
    print(f"\n--- ▶️ Ejecutando Tarea: '{task_name}' ---")
    task = TASK_REGISTRY[task_name]

    if task.get("needs_pdf_path", False):
        extractor_function = task["extractor_func"]
        return extractor_function(pdf_path)

    if not task["search_queries"]:
        return None

    collection_name = f"source_{document_info.source.lower()}"
    relevant_chunks = set()
    for query in task["search_queries"]:
        try:
            # Búsqueda semántica con Qdrant
            results = qdrant_manager.search(collection_name, query)
            # Extraemos el texto de los resultados
            for res in results:
                if 'content' in res:
                    relevant_chunks.add(res['content'])
        except Exception as e:
            print(f"⚠️ Error en búsqueda para query '{query}': {e}")
            continue
    
    if not relevant_chunks:
        print(f"⚠️ No se encontraron chunks relevantes para la tarea '{task_name}'.")
        return None

    contexto_para_extraccion = "\n\n---\n\n".join(list(relevant_chunks))
    extractor_function = task["extractor_func"]
    
    try:
        return extractor_function(contexto_para_extraccion)
    except Exception as e:
        print(f"❌ Error ejecutando extractor para '{task_name}': {e}")
        return None

# 4. El orquestador ahora indexa en Qdrant
def process_pdf_automatically(pdf_path: str, doc_hash: str): # Añadimos doc_hash como parámetro
    """Orquestador que clasifica, indexa en Qdrant y ejecuta tareas."""
    print(f"--- 🚀 Iniciando Procesamiento Automático para: {os.path.basename(pdf_path)} ---")

    # --- Clasificación (sin cambios) ---
    reader = PdfReader(pdf_path)
    first_page_text = reader.pages[0].extract_text().strip()
    document_info = classify_with_ai(first_page_text)
    print(f"\n✅ Documento clasificado como: '{document_info.source}' '{document_info.date}'")
    
    # --- Indexación en Qdrant ---
    collection_name = f"source_{document_info.source.lower()}"
    qdrant_manager.get_or_create_collection(collection_name)
    
    all_chunks = get_pdf_chunks(pdf_path)
    pdf_filename = os.path.basename(pdf_path)
    
    # Preparamos los datos para Qdrant: IDs, vectores (implícito) y metadatos (payload)
    ids = [f"{doc_hash}_{i}" for i in range(len(all_chunks))] # Usamos el hash para los IDs
    metadata = [{
        "document_hash": doc_hash, # Guardamos el hash en los metadatos
        "document_id": pdf_filename, 
        "chunk_index": i, 
        "content": chunk,
        "source": document_info.source,
        "document_date": document_info.date.isoformat()
    } for i, chunk in enumerate(all_chunks)]
    
    qdrant_manager.upsert_chunks(collection_name, all_chunks, metadata, ids)

    # Si es 'Other', solo indexamos y terminamos.
    if document_info.source == "Other":
        print("Documento de tipo 'Other' indexado. No se ejecutan tareas.")
        return {"status": "indexed_as_other", "source": "Other"}

    # --- Ejecución de Tareas (la lógica principal no cambia) ---
    tasks_to_run = [
        task_name for task_name, task_details in TASK_REGISTRY.items()
        if task_details["source"] == document_info.source
    ]

    if not tasks_to_run:
        print(f"⚠️ No se encontraron tareas definidas para la fuente '{document_info.source}'.")
        return {"status": "no_tasks_found", "source": document_info.source}

    print(f"\n▶️ Tareas a ejecutar para '{document_info.source}': {', '.join(tasks_to_run)}")
    
    resultados_finales = {}
    for task_name in tasks_to_run:
        try:
            # Llamamos a run_task sin el objeto 'collection'
            resultado_tarea = run_task(document_info, task_name, pdf_path)
            
            if hasattr(resultado_tarea, 'model_dump'):
                resultado_dict = resultado_tarea.model_dump()
            else:
                resultado_dict = resultado_tarea if resultado_tarea is not None else {}

            fecha_str = document_info.date.isoformat() if isinstance(document_info.date, date) else str(document_info.date)

            def convert_dates_to_iso(obj):
                if isinstance(obj, dict): return {k: convert_dates_to_iso(v) for k, v in obj.items()}
                if isinstance(obj, list): return [convert_dates_to_iso(i) for i in obj]
                if isinstance(obj, date): return obj.isoformat()
                return obj

            resultados_finales[task_name] = convert_dates_to_iso(resultado_dict)
            resultados_finales[task_name]["fecha"] = fecha_str
            resultados_finales[task_name]["fuente"] = document_info.source
        except Exception as e:
            print(f"❌ Error en la tarea '{task_name}': {e}")
            resultados_finales[task_name] = {"error": str(e)}

    # --- Resultados (sin cambios) ---
    print("\n\n" + "="*50)
    print("--- 🎯 RESULTADOS FINALES CONSOLIDADOS ---")
    print(json.dumps(resultados_finales, indent=2))
    print("="*50)

    return resultados_finales