# ---- Etapa 1: Builder ----
# En esta etapa instalamos todo, incluyendo las herramientas de compilación
FROM python:3.11 AS builder

WORKDIR /usr/src/app

# Instalar herramientas de compilación
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Instalar las dependencias de Python en un entorno virtual
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --no-deps --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Antes de tu "pip install"
RUN apt-get update && apt-get install -y gnupg2
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc


# ---- Etapa 2: Imagen Final ----
# Esta es la imagen que se ejecutará. Es mucho más ligera.
FROM python:3.11-slim

WORKDIR /usr/src/app

# --- INICIO: Instalar Drivers, netcat y otras herramientas ---
# Añadimos 'netcat-openbsd' para nuestro script de espera.
RUN apt-get update && apt-get install -y curl gnupg ca-certificates netcat-openbsd && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# --- FIN: Instalar Drivers, netcat y otras herramientas ---


# Establecer PYTHONPATH para que las importaciones 'from app...' funcionen
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

# Copiar solo el entorno virtual con las dependencias instaladas de la etapa "builder"
COPY --from=builder /opt/venv /opt/venv

# Copiar el código de la aplicación y el script de espera
COPY ./app ./app
COPY ./main.py .
COPY wait-for-db.sh .

# Dar permisos de ejecución al script
RUN chmod +x wait-for-db.sh

# Activar el entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación, esperando primero a la BD
CMD ["./wait-for-db.sh", "sqlserver_db", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]