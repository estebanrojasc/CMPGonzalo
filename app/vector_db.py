import qdrant_client
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import os
import numpy as np

class QdrantManager:
    def __init__(self):
        self.client = qdrant_client.QdrantClient(
            url=os.getenv("QDRANT_URL"), 
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        # Usar un modelo de embedding más ligero y rápido si es posible
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()

    def get_or_create_collection(self, collection_name: str):
        try:
            self.client.get_collection(collection_name=collection_name)
            print(f"Colección '{collection_name}' ya existe.")
        except Exception:
            print(f"Creando colección '{collection_name}'...")
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
            )

    def check_document_exists(self, collection_name: str, doc_hash: str) -> bool:
        """Verifica si un documento con un hash específico ya ha sido procesado."""
        try:
            # Hacemos un scroll con un filtro para buscar cualquier punto con este hash
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_hash",
                            match=models.MatchValue(value=doc_hash),
                        )
                    ]
                ),
                limit=1, # Solo necesitamos saber si existe al menos uno
            )
            # Si la lista de resultados no está vacía, el documento existe.
            return len(scroll_result[0]) > 0
        except Exception:
            # Si la colección no existe o hay otro error, asumimos que no existe.
            return False

    def upsert_chunks(self, collection_name: str, chunks: list[str], metadata: list[dict], ids: list[str]):
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=True)
        
        self.client.upsert(
            collection_name=collection_name,
            points=models.Batch(
                ids=ids,
                vectors=embeddings.tolist(),
                payloads=metadata
            ),
            wait=True
        )
        print(f"Upsert de {len(chunks)} chunks completado.")

    def search(self, collection_name: str, query_text: str, top_k: int = 5) -> list[dict]:
        query_vector = self.embedding_model.encode(query_text).tolist()
        
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True # Para que devuelva los metadatos
        )
        
        # Extraer solo el contenido del payload
        return [hit.payload for hit in search_result] 