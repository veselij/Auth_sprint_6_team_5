hey -m POST -T "application/json" -d '{"login":"zadmin123","password":"zadmin123"}' http://127.0.0.1:5000/users/login

python -m gunicorn --worker-class=gevent --workers=1  --threads 5 --bind 0.0.0.0:5001 wsgi_app:app

alembic upgrade head