#!/bin/sh

echo "Waiting for API..."
while ! nc -z $API_IP $API_IP_PORT; do
  sleep 0.1
done
echo "API started"

echo "starting tests"
python -m pytest src/
echo "tests finished"


exec "$@"

