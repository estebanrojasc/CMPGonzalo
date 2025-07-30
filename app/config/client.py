import instructor
from openai import OpenAI, AzureOpenAI

from app.config.settings import (
    OPENAI_PROVIDER,
    OPENAI_API_KEY,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT, # Importamos el deployment
)

def get_openai_config():
    """
    Determina el proveedor y devuelve el cliente de OpenAI (estándar o Azure)
    y el nombre del modelo/deployment a usar.
    """
    provider = OPENAI_PROVIDER.lower()
    
    if provider == "azure":
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT]):
            raise ValueError("Para 'azure', se requieren AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_DEPLOYMENT.")
        
        print("💡 Usando proveedor: Azure OpenAI")
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-05-01-preview",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )
        model = AZURE_OPENAI_DEPLOYMENT
    
    elif provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("Para 'openai', se requiere la variable OPENAI_API_KEY.")
            
        print("💡 Usando proveedor: OpenAI (API directa)")
        client = OpenAI(api_key=OPENAI_API_KEY)
        model = "gpt-4o-mini" # Modelo por defecto para OpenAI
        
    else:
        raise ValueError(f"Proveedor de OpenAI no válido: '{provider}'. Debe ser 'openai' o 'azure'.")

    # Devolvemos el cliente "parcheado" por instructor y el nombre del modelo
    return instructor.patch(client), model

# Llamamos a la función una vez y exportamos las variables para ser usadas en el resto de la app
client, model_name = get_openai_config() 