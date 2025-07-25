# Usar una imagen base más ligera
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /usr/src/app

# Instalar solo las dependencias esenciales del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar solo los archivos necesarios para instalar dependencias
COPY requirements.txt .

# Instalar dependencias de Python optimizando espacio
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip/*

# Crear directorio para ChromaDB
RUN mkdir -p /usr/src/app/chroma_db

# Copiar solo los archivos necesarios de la aplicación
COPY ./app ./app
COPY ./main.py .

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]