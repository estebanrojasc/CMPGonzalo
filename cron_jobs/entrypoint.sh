#!/bin/sh

# Crear un archivo de log específico para cron si no existe.
touch /var/log/cron.log

# Iniciar el demonio de cron en segundo plano, diciéndole que escriba en nuestro archivo.
crond -L /var/log/cron.log

# Mostrar los logs de cron en tiempo real para que 'docker-compose logs' funcione.
# Esto también mantiene el contenedor corriendo en primer plano.
tail -f /var/log/cron.log 