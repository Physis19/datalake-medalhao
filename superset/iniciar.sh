#!/bin/sh
set -e

superset db upgrade
# Se o admin já existir, o comando apenas avisa
superset fab create-admin --username admin --firstname Admin --lastname User \
  --email admin@example.com --password "$SUPERSET_ADMIN_PASSWORD"
superset init
python /opt/datalake/superset/empacotar.py /tmp/dashboard.zip
superset import-dashboards --path /tmp/dashboard.zip --username admin

exec /usr/bin/run-server.sh
