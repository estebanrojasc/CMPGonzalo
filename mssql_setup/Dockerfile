# Usar una imagen base ligera de Alpine
# Usamos la imagen oficial de Microsoft como base
FROM mcr.microsoft.com/mssql/server:2019-latest

# --- INICIO: Cambios de Permisos ---
# Cambiar temporalmente al usuario root para poder instalar paquetes
USER root
# --- FIN: Cambios de Permisos ---

# Instalar las herramientas de línea de comandos (sqlcmd) y otras dependencias
RUN apt-get update && apt-get install -y curl gnupg ca-certificates && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64] https://packages.microsoft.com/ubuntu/20.04/prod focal main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Crear un directorio de trabajo para nuestros scripts
WORKDIR /usr/src/app

# Copiar nuestros scripts al contenedor
COPY setup.sql .
COPY entrypoint.sh .

# Hacer ejecutable nuestro script de entrada
RUN chmod +x entrypoint.sh

# --- INICIO: Cambios de Permisos ---
# Volver al usuario por defecto de la imagen para la ejecución (mejor práctica de seguridad)
USER mssql
# --- FIN: Cambios de Permisos ---

# Establecer nuestro script como el punto de entrada
ENTRYPOINT ["/bin/bash", "entrypoint.sh"] 