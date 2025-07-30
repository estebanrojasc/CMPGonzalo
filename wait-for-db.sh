#!/bin/sh
# wait-for-db.sh

set -e

# El host de la BD se pasa como primer argumento, el resto son el comando a ejecutar
host="$1"
shift
cmd="$@"

# Bucle que intenta conectar con el host de la BD en el puerto 1433.
# Se detiene cuando la conexión es exitosa.
# `nc` es una herramienta de red (netcat) que usaremos para esto.
until nc -z -v -w30 "$host" 1433; do
  >&2 echo "SQL Server no está disponible. Reintentando en 1 segundo..."
  sleep 1
done

>&2 echo "✅ SQL Server está listo. Ejecutando la aplicación..."
exec $cmd 