from gevent import monkey

monkey.patch_all()

import psycogreen.gevent

psycogreen.gevent.patch_psycopg()

from main import create_app

app = create_app()
