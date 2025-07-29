import hashlib
from azure.storage.blob import BlobServiceClient
import os
from typing import Tuple

from app.config.settings import *


class BlobStorage:
    def __init__(self):
        self.connection_string = AZURE_STORAGE_CONNECTION_STRING
        self.container_name = AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)

    def generar_hash_pdf(self, file_path: str, num_bytes: int = 500) -> str:
        with open(file_path, 'rb') as f:
            data = f.read(num_bytes)
        return hashlib.sha1(data).hexdigest()

    def existe_blob_con_hash(self, hash_val: str, fuente: str) -> bool:
        blob_prefix = f"{fuente}/"
        for blob in self.container_client.list_blobs(name_starts_with=blob_prefix):
            if hash_val in blob.name:
                return True
        return False

    def upload_file(self, file_path: str, fuente: str) -> Tuple[bool, str]:
        """
        Sube un archivo al blob storage si no existe.
        Returns: (éxito, mensaje)
        """
        try:
            hash_val = self.generar_hash_pdf(file_path)
            blob_prefix = f"{fuente}/"
            blob_name = f"{blob_prefix}{hash_val}_{os.path.basename(file_path)}"

            if self.existe_blob_con_hash(hash_val, fuente):
                return False, "El archivo ya existe en el storage"

            blob_client = self.container_client.get_blob_client(blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=False)
            return True, f"Archivo subido exitosamente como {blob_name}"

        except Exception as e:
            return False, f"Error subiendo archivo: {str(e)}"

    def get_blob_url(self, blob_name: str) -> str:
        """Obtiene la URL del blob"""
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.url