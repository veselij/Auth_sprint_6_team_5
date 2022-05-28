from gevent import monkey

monkey.patch_all()

import psycogreen.gevent

psycogreen.gevent.patch_psycopg()

from main import create_app
from social.oauth import oauth

app = create_app()
oauth.init_app(app)
