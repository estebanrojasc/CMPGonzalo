import os
from dotenv import load_dotenv

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Token de seguridad para la API
API_SECURITY_TOKEN = os.getenv("API_SECURITY_TOKEN")

# Proveedor de OpenAI ('openai' o 'azure')
OPENAI_PROVIDER = os.getenv("OPENAI_PROVIDER", "openai")

# Configuración para Azure OpenAI (si se usa)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# SQL Server (nuevo)
MSSQL_HOST = os.getenv("DB_HOST", "sqlserver_db") # El nombre del servicio en docker-compose
MSSQL_USER = os.getenv("MSSQL_USER", "sa")
MSSQL_PASSWORD = os.getenv("MSSQL_SA_PASSWORD", "tu_super_password")
MSSQL_DB = os.getenv("MSSQL_DB", "CMP_Gonzalo_DB") # Debes crear esta base de datos
MSSQL_DRIVER = '{ODBC Driver 17 for SQL Server}' # Depende del driver instalado en tu Dockerfile
