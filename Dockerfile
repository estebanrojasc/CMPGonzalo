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
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt


# ---- Etapa 2: Imagen Final ----
# Esta es la imagen que se ejecutará. Es mucho más ligera.
FROM python:3.11-slim

WORKDIR /usr/src/app

# Establecer PYTHONPATH para que las importaciones 'from app...' funcionen
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

# Copiar solo el entorno virtual con las dependencias instaladas de la etapa "builder"
COPY --from=builder /opt/venv /opt/venv

# Copiar el código de la aplicación
COPY ./app ./app
COPY ./main.py .

# Activar el entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
# Nota: --reload no se recomienda en producción. Quítalo para despliegues reales.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]