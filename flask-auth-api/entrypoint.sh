#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z $PG_HOST $PG_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Apply migration"
alembic upgrade head

echo "Create super user and collectstatic"
python -m flask superuser create --no-interactive

echo "Start gunicorn server"
python -m gunicorn --worker-class=gevent --workers=1 --bind 0.0.0.0:$API_IP_PORT wsgi_app:app

exec "$@"

