#!/bin/sh
# backup.sh - Script para respaldar todas las colecciones de Qdrant.

# crond ya se encarga del logging básico. Este script será más explícito.
echo "--- [$(date)] Iniciando proceso de respaldo de Qdrant ---"

# 1. Obtener la lista de colecciones.
COLLECTION_LIST=$(curl -s -X GET http://qdrant:6333/collections | jq -r '.result.collections[].name')

if [ -z "$COLLECTION_LIST" ]; then
    echo "No se encontraron colecciones para respaldar. Terminando."
    echo "--- [$(date)] Proceso de respaldo finalizado ---"
    exit 0
fi

echo "Colecciones encontradas para respaldar:"
echo "$COLLECTION_LIST"

# 2. Iterar sobre cada colección y crear un snapshot.
for COLLECTION_NAME in $COLLECTION_LIST
do
    echo "-> Creando snapshot para la colección: '$COLLECTION_NAME'..."
    # Usamos -f para que curl falle con un código de error si la API devuelve un error HTTP (ej. 4xx o 5xx)
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "http://qdrant:6333/collections/${COLLECTION_NAME}/snapshots")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        echo "   ✅ Solicitud de snapshot para '$COLLECTION_NAME' enviada con éxito (Código: $HTTP_CODE)."
    else
        echo "   ❌ ERROR al solicitar snapshot para '$COLLECTION_NAME' (Código: $HTTP_CODE)."
    fi
done

echo "--- [$(date)] Proceso de respaldo finalizado ---" 