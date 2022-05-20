from gevent import monkey

monkey.patch_all()

import psycogreen.gevent

psycogreen.gevent.patch_psycopg()

from main import app
