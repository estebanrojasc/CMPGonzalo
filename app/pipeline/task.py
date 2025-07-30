from app.ai.classify import classify_with_ai, DocumentSource
from app.ai.extract_data import EXTRACTORS
from app.ai.extract_graphs import extraer_graficos_mysteel
from app.services.vector_db import QdrantManager
from app.services.db_manager import db_manager
from app.config.settings import *
from datetime import datetime
import traceback
import os
import time
import uuid
from PyPDF2 import PdfReader
from app.pipeline.utils import get_pdf_chunks, _serialize_special_types

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
        "extractor_func": EXTRACTORS["extraer_noticias"],
        "search_queries": ["news", "market commentary", "outlook"],
        "needs_pdf_path": False
    },
    "get_mysteel_graphs": {
        "source": "Mysteel",
        "extractor_func": extraer_graficos_mysteel,
        "search_queries": [], # No necesita búsqueda semántica
        "needs_pdf_path": True # Necesita la ruta del archivo para PyMuPDF
    },
    
    # Platts
    "get_platts_prices": {
        "source": "Platts",
        "search_queries": ["Tabla o texto con los precios de Iron Ore Platts 62% y 65% CFR China con su fecha", "Tabla o texto con los precios de IOMGD00 con su fecha"],
        "extractor_func": EXTRACTORS["Platts"]
    },
    # "get_platts_news": {
    #     "source": "Platts",
    #     "extractor_func": EXTRACTORS["extraer_noticias"],
    #     "search_queries": ["news", "market commentary", "outlook", "platts news"],
    #     "needs_pdf_path": False
    # },
    "get_fastmarkets_prices": {
        "source": "FastMarkets",
        "search_queries": ["Tabla o texto con los precios de Iron Ore MB-IRO-0009 y MB-IRO-0019 VIU con su fecha de publicación"],
        "extractor_func": EXTRACTORS["FastMarkets"]
    },
    # "get_fastmarkets_news": {
    #     "source": "FastMarkets",
    #     "extractor_func": EXTRACTORS["extraer_noticias"],
    #     "search_queries": ["news", "market commentary", "outlook", "fastmarkets news"],
    #     "needs_pdf_path": False
    # },
    "get_baltic_prices": {
        "source": "Baltic",
        "search_queries": ["Tabla o texto con el precio del flete C3 Tubarao to Qingdao con su fecha"],
        "extractor_func": EXTRACTORS["Baltic"]
    },
    # "get_baltic_news": {
    #     "source": "Baltic",
    #     "extractor_func": EXTRACTORS["extraer_noticias"],
    #     "search_queries": ["news", "freight market", "baltic dry index"],
    #     "needs_pdf_path": False
    # },
}

# 3. La función `run_task` ahora incluye logging
def run_task(document_id: int, document_info: DocumentSource, task_name: str, qdrant_manager: QdrantManager, pdf_path: str = None):
    """Ejecuta una tarea individual, mide su tiempo y registra el resultado."""
    print(f"\n--- ▶️ Ejecutando Tarea: '{task_name}' ---")
    task = TASK_REGISTRY[task_name]
    start_time = datetime.now()
    
    error_msg = None
    resultado_tarea = None
    num_resultados = 0
    estado = "ERROR"

    try:
        extractor_function = task["extractor_func"]
        
        if task.get("needs_pdf_path", False):
            contexto_para_extraccion = pdf_path
        else:
            if not task["search_queries"]:
                return None
            
            collection_name = f"source_{document_info.source.lower()}"
            relevant_chunks = set()
            for query in task["search_queries"]:
                results = qdrant_manager.search(collection_name, query)
                for res in results:
                    if 'content' in res: relevant_chunks.add(res['content'])
            
            if not relevant_chunks:
                print(f"⚠️ No se encontraron chunks relevantes para la tarea '{task_name}'.")
                estado = "SUCCESS_NO_DATA"
                return None

            contexto_para_extraccion = "\n\n---\n\n".join(list(relevant_chunks))
        
        resultado_tarea = extractor_function(contexto_para_extraccion)
        estado = "SUCCESS"

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error ejecutando extractor para '{task_name}': {e}")
        traceback.print_exc()

    finally:
        end_time = datetime.now()
        # Contar resultados (esto es una heurística, puede necesitar ajuste)
        if resultado_tarea:
            # Convertir a dict si es un modelo Pydantic para poder iterar
            resultado_dict = resultado_tarea
            if not isinstance(resultado_tarea, dict) and hasattr(resultado_tarea, 'model_dump'):
                resultado_dict = resultado_tarea.model_dump()
            elif not isinstance(resultado_tarea, dict) and hasattr(resultado_tarea, 'dict'):
                resultado_dict = resultado_tarea.dict()

            num_resultados = 0
            if isinstance(resultado_dict, dict):
                for val in resultado_dict.values():
                    if isinstance(val, list):
                        num_resultados += len(val)
        
        db_manager.log_tarea(
            documento_id=document_id,
            nombre_tarea=task_name,
            estado=estado,
            inicio=start_time,
            fin=end_time,
            resultados_encontrados=num_resultados,
            error_mensaje=error_msg
        )

    return resultado_tarea


# 4. El orquestador ahora tiene logging extensivo
def process_pdf_automatically(pdf_path: str, doc_hash: str, qdrant_manager: QdrantManager):
    """Orquestador que clasifica, indexa en Qdrant, ejecuta tareas y registra todo en la BD."""
    print(f"--- 🚀 Iniciando Procesamiento Automático para: {os.path.basename(pdf_path)} ---")
    
    # --- Clasificación y guardado inicial del documento ---
    start_time = time.time()
    try:
        reader = PdfReader(pdf_path)
        first_page_text = reader.pages[0].extract_text().strip()
        document_info = classify_with_ai(first_page_text)
        print(f"\n✅ Documento clasificado como: '{document_info.source}' '{document_info.date}'")
    except Exception as e:
        print(f"Error Crítico en Clasificación: {e}")
        # No podemos continuar si no podemos clasificar
        return {"status": "error_classification", "error": str(e)}

    # --- Guardar en Base de Datos PostgreSQL y obtener ID ---
    document_id = db_manager.save_document(
        nombre_archivo=os.path.basename(pdf_path),
        fecha_documento=document_info.date,
        fuente=document_info.source,
        hash_documento=doc_hash
    )

    if not document_id:
        print(f"🛑 El documento con hash {doc_hash[:10]}... ya existe en la base de datos. Se detiene el procesamiento.")
        return {"status": "skipped_duplicate_in_db", "hash": doc_hash}

    dur_ms = int((time.time() - start_time) * 1000)
    db_manager.log_procesamiento_evento(document_id, "Clasificación", "SUCCESS", dur_ms)

    # --- Indexación en Qdrant ---
    start_time = time.time()
    try:
        collection_name = f"source_{document_info.source.lower()}"
        qdrant_manager.get_or_create_collection(collection_name)
        
        all_chunks = get_pdf_chunks(pdf_path)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_hash}-{i}")) for i in range(len(all_chunks))]
        metadata = [{"document_hash": doc_hash, "document_id": os.path.basename(pdf_path), "chunk_index": i, "content": chunk, "source": document_info.source, "document_date": document_info.date.isoformat()} for i, chunk in enumerate(all_chunks)]
        qdrant_manager.upsert_chunks(collection_name, all_chunks, metadata, ids)
        
        dur_ms = int((time.time() - start_time) * 1000)
        db_manager.log_procesamiento_evento(document_id, "Indexación Qdrant", "SUCCESS", dur_ms, detalles={"chunks": len(all_chunks)})
    except Exception as e:
        dur_ms = int((time.time() - start_time) * 1000)
        db_manager.log_procesamiento_evento(document_id, "Indexación Qdrant", "ERROR", dur_ms, error_mensaje=str(e))
        print(f"Error en Indexación: {e}")
        return {"status": "error_indexing", "error": str(e)}

    if document_info.source == "Other":
        print("Documento de tipo 'Other' indexado. No se ejecutan tareas.")
        return {"status": "indexed_as_other", "source": "Other"}

    # --- Ejecución de Tareas ---
    start_time = time.time()
    tasks_to_run = [
        task_name for task_name, task_details in TASK_REGISTRY.items()
        if task_details["source"] == document_info.source
    ]
    
    resultados_finales = {}
    if tasks_to_run:
        print(f"\n▶️ Tareas a ejecutar para '{document_info.source}': {', '.join(tasks_to_run)}")
        for task_name in tasks_to_run:
            # Pasamos el document_id a run_task para el logging
            resultado_tarea = run_task(document_id, document_info, task_name, qdrant_manager, pdf_path=pdf_path)
            if resultado_tarea:
                # Convertir Pydantic a dict y asegurar que los tipos especiales sean serializables
                dumped_result = resultado_tarea.model_dump() if hasattr(resultado_tarea, 'model_dump') else resultado_tarea
                resultados_finales[task_name] = _serialize_special_types(dumped_result)

    dur_ms = int((time.time() - start_time) * 1000)
    db_manager.log_procesamiento_evento(document_id, "Ejecución de Tareas", "SUCCESS", dur_ms, detalles={"tareas_ejecutadas": len(tasks_to_run)})

    # --- Guardar resultados en PostgreSQL ---
    start_time = time.time()
    print("\n--- 💾 Guardando resultados en la Base de Datos... ---")
    
    # Pasamos la fecha del documento como fallback
    db_manager.save_results_to_db(document_id, document_info.source, document_info.date, resultados_finales)
    
    dur_ms = int((time.time() - start_time) * 1000)
    db_manager.log_procesamiento_evento(document_id, "Guardado en DB", "SUCCESS", dur_ms)
    print("--- ✅ Proceso Finalizado ---")

    return _serialize_special_types(resultados_finales)