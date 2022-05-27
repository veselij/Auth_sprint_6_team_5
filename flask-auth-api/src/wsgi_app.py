from gevent import monkey

monkey.patch_all()

import psycogreen.gevent

psycogreen.gevent.patch_psycopg()

from main import create_app
from social.oauth import oauth, testing_oauth

app = create_app()
if app.config["TESTING"]:
    testing_oauth.init_app(app)
else:
    oauth.init_app(app)
