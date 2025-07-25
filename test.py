import os
from openai import AzureOpenAI

try:
    print("--- Iniciando prueba de conexión simple ---")
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, azure_endpoint, deployment_name]):
        print("❌ ERROR: Faltan una o más variables de entorno (AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT).")
    else:
        client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-05-01-preview",
            azure_endpoint=azure_endpoint,
        )

        print(f"Endpoint: {azure_endpoint}")
        print(f"Deployment: {deployment_name}")

        print("Realizando llamada a chat.completions.create...")
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": "Hello, world!"}],
            max_tokens=10
        )

        print("\n✅ ¡ÉXITO! La conexión y la llamada básica funcionan.")
        print("Respuesta del modelo:", response.choices[0].message.content)

except Exception as e:
    print(f"\n❌ ERROR: La prueba de conexión falló.")
    print("Detalle del error:", e)