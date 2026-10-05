#!/usr/bin/env bash
# Comando de build en Render: instala dependencias, junta los estáticos y aplica migraciones.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
