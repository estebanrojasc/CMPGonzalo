from azure.storage.blob import BlobServiceClient
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Parámetros de conexión
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
# local_file_path = "app\Mysteel Raw Materials Daily 20241128.pdf"  # El PDF que quieres subir
# blob_name = "app/73ab2b715e09fc89f26098cc02073ef5378bf148_Mysteel Raw Materials Daily 20241128.pdf"  # Nombre con que se guardará en el contenedor

# Conectar
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
#blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

# def upload_file(file_path):
#     with open(file_path, "rb") as data:
#         blob_client.upload_blob(data, overwrite=True)
#         print("✅ PDF cargado correctamente.")

# container_client = blob_service_client.get_container_client(container_name)

# print("📂 Archivos en el contenedor:")
# for blob in container_client.list_blobs():
#     print(" -", blob.name)

# # Eliminar el blob
# blob_client.delete_blob()
# print("🗑️ PDF eliminado correctamente.")



# Eliminar todos los blobs (archivos) del contenedor
container_client = blob_service_client.get_container_client(container_name)

print("Eliminando todos los blobs del contenedor...")
for blob in container_client.list_blobs():
    print(f"Eliminando: {blob.name}")
    blob_to_delete = container_client.get_blob_client(blob)
    blob_to_delete.delete_blob()
print("✅ Todos los blobs han sido eliminados.")

