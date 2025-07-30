# Usar una imagen base ligera de Alpine
FROM alpine:latest

# Instalar las herramientas necesarias: cron, curl y jq
RUN apk add --no-cache curl dcron jq

# Copiar nuestro script de backup y darle permisos
COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Copiar nuestro archivo de definición de cron
COPY qdrant-backup-cron /etc/crontabs/root

# --- INICIO: Corregir formato de crontab ---
# Asegurar que no tenga finales de línea de Windows (CRLF) y que termine con una línea nueva.
# Esto hace la configuración robusta independientemente de cómo se edite el archivo.
RUN sed -i 's/\r$//' /etc/crontabs/root && echo "" >> /etc/crontabs/root
# --- FIN: Corregir formato de crontab ---

RUN chmod 0644 /etc/crontabs/root

# Copiar el nuevo script de punto de entrada y darle permisos
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Establecer nuestro nuevo script como el punto de entrada
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"] 