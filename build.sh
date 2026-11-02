#!/usr/bin/env bash
# Comando de build en Render: instala dependencias, junta los estáticos y aplica migraciones.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py crear_admin
python manage.py poblar_datos
# Datos de ejemplo al día (borra pagos, reservas, visitas... y los crea con fechas de hoy).
# Solo si en Render se define REFRESCAR_DATOS=1; quítala después del deploy.
if [ "${REFRESCAR_DATOS:-0}" = "1" ]; then
    python manage.py refrescar_datos --si
fi
