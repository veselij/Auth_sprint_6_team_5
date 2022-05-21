from gevent import monkey

monkey.patch_all()

import psycogreen.gevent

psycogreen.gevent.patch_psycopg()

from gevent.pywsgi import WSGIServer

from main import app

http_server = WSGIServer(("", 5001), app)
http_server.serve_forever()
