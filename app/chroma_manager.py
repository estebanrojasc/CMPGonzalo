from azure.storage.blob import BlobServiceClient
import chromadb
import os

class ChromaAzureManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.container_name = "chroma-db"
        self.local_path = "/usr/src/app/chroma_db"
        
        # Asegurarse que el directorio local existe
        os.makedirs(self.local_path, exist_ok=True)
        
        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(path=self.local_path)
        
        # Conectar con Azure
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.container = self.blob_service.get_container_client(self.container_name)

    def sync_from_azure(self):
        """Descarga la base de datos desde Azure"""
        blobs = self.container.list_blobs()
        for blob in blobs:
            blob_client = self.container.get_blob_client(blob.name)
            download_path = os.path.join(self.local_path, blob.name)
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            with open(download_path, "wb") as f:
                f.write(blob_client.download_blob().readall())

    def backup_to_azure(self):
        """Sube la base de datos a Azure"""
        for root, _, files in os.walk(self.local_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                blob_path = os.path.relpath(local_file_path, self.local_path)
                blob_client = self.container.get_blob_client(blob_path)
                with open(local_file_path, "rb") as f:
                    blob_client.upload_blob(f, overwrite=True) 