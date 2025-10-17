#!/usr/bin/env bash
set -euo pipefail

python manage.py makemigrations --noinput || true
python manage.py migrate --noinput
python manage.py collectstatic --no-input
python _deploy/init_scripts.py

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf