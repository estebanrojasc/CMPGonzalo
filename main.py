from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, Any
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
import base64
import hashlib
from app.config.settings import *
from app.services.file_storage import BlobStorage
from app.services.vector_db import QdrantManager
from app.ai.classify import classify_with_ai
from app.ai.extract_text import extract_first_page_text
from app.pipeline.task import process_pdf_automatically
from app.pipeline.utils import sanitize_for_logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFPayload(BaseModel):
    name: str
    contentBytes: str  # Contenido del archivo en Base64
    contentType: str

# Crear instancia global de BlobStorage
blob_storage = None
qdrant_manager = None  # Nueva variable global

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar
    global blob_storage
    global qdrant_manager
    logger.info("Iniciando aplicación...")
    try:
        blob_storage = BlobStorage()
        qdrant_manager = QdrantManager()
        logger.info("Conexiones a Blob Storage y Qdrant establecidas")
        yield
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}")
        raise
    finally:
        # Código que se ejecuta al cerrar
        logger.info("Cerrando aplicación...")

app = FastAPI(
    title="PDF Processor API",
    description="Procesa PDFs usando clasificación automática y extracción estructurada.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def cleanup_temp_file(file_path: str):
    """Limpia archivos temporales de forma segura"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Archivo temporal eliminado: {file_path}")
    except Exception as e:
        logger.error(f"Error eliminando archivo temporal {file_path}: {e}")

def get_file_hash(file_path: str) -> str:
    """Calcula el hash SHA256 de un archivo."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@app.post("/procesar_pdf")
async def procesar_pdf(payload: PDFPayload) -> Dict[str, Any]:
    if "pdf" not in payload.contentType.lower():
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    temp_file_path = None
    try:
        # 1. Decodificar Base64 y guardar archivo temporalmente
        file_content = base64.b64decode(payload.contentBytes)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_content)
            temp_file_path = tmp.name
            logger.info(f"Archivo temporal creado: {temp_file_path}")

        # 2. Clasificar y calcular Hash
        first_page_text = extract_first_page_text(temp_file_path)
        classification = classify_with_ai(first_page_text)
        file_hash = get_file_hash(temp_file_path)
        
        collection_name = f"source_{classification.source.lower()}"

        # 3. VERIFICAR DUPLICADOS EN QDRANT ANTES DE PROCESAR
        if qdrant_manager.check_document_exists(collection_name, file_hash):
            raise HTTPException(
                status_code=409, # 409 Conflict
                detail=f"Documento con hash {file_hash[:10]}... ya existe en la colección '{collection_name}'."
            )

        # 4. Subir a Azure Blob Storage (opcional pero recomendado como backup)
        success, message = blob_storage.upload_file(temp_file_path, classification.source.lower())
        
        if not success:
            if "ya existe" in message:
                logger.warning(f"Documento duplicado: {payload.name}")
                raise HTTPException(
                    status_code=409,
                    detail={
                        "mensaje": "Este documento ya fue procesado anteriormente",
                        "detalles": message
                    }
                )
            logger.error(f"Error al subir archivo: {message}")
            raise HTTPException(status_code=500, detail=message)

        # 5. Procesar el documento (solo si es nuevo)
        logger.info("Iniciando procesamiento del documento...")
        resultados = process_pdf_automatically(temp_file_path, file_hash, qdrant_manager)

        # 6. Preparar respuesta
        response = {
            "estado": "éxito",
            "clasificacion": {
                "fuente": classification.source,
                "fecha": classification.date.isoformat()
            },
            "almacenamiento": {
                "mensaje": message
            },
            "resultados": resultados
        }

        # Usamos nuestra función para sanear la respuesta
        sanitized_response = sanitize_for_logging(response)
        
        # Logueamos la versión saneada
        logger.info(f"Procesamiento completado. Respuesta: {json.dumps(sanitized_response, indent=2)}")
        
        # Devolvemos la RESPUESTA SANEADA, con el base64 ya truncado
        return JSONResponse(content=sanitized_response, status_code=200)

    except HTTPException as he:
        # Re-lanzar excepciones HTTP
        raise

    except Exception as e:
        logger.error(f"Error procesando documento: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "mensaje": "Error interno del servidor",
                "detalles": str(e)
            }
        )

    finally:
        # Limpiar archivo temporal
        if temp_file_path:
            await cleanup_temp_file(temp_file_path)

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    try:
        # Verificar conexión a Blob Storage
        if not blob_storage:
            raise Exception("Blob Storage no inicializado")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "blob_storage": "connected"
        }
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e)
            }
        )
