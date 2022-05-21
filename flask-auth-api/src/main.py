from datetime import timedelta

from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager

import api.v1.users as users_api
from commands.superuser import superuser_cli
from core.config import config
from db.db import init_db

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = config.secret
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=config.access_ttl)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(seconds=config.refresh_ttl)
jwt = JWTManager(app)


app.cli.add_command(superuser_cli)

app.register_blueprint(users_api.bp)

app.config["SWAGGER"] = {"title": config.api_name, "uiversion": config.uiversion, "openapi": config.openapi}
swag = Swagger(app)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, threaded=True)
