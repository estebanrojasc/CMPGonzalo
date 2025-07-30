#!/bin/bash
set -e

# Iniciar el proceso de SQL Server en segundo plano
/opt/mssql/bin/sqlservr &

# Esperar a que SQL Server esté listo para aceptar conexiones
echo "⏳ Esperando a que SQL Server se inicie..."
until /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -Q "SELECT 1" &> /dev/null; do
  echo -n "."
  sleep 1
done

echo -e "\n✅ SQL Server está listo."

# Ejecutar el script de configuración, pasando el nombre de la BD como una variable.
echo "🚀 Ejecutando script de configuración (setup.sql) en la base de datos: ${MSSQL_DB}..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -d master -i /usr/src/app/setup.sql -v DB_NAME="${MSSQL_DB}"

echo "🎉 ¡Base de datos y tablas configuradas!"

# Esperar a que el proceso de SQL Server en segundo plano termine
wait 