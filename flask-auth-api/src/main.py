from datetime import timedelta

from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager

import api.v1.request as request_api
import api.v1.roles as roles_api
import api.v1.users as users_api
from commands.superuser import superuser_cli
from containers.container import Container
from core.config import SWAGGER_TEMPLATE, config
from social.oauth import oauth
from utils.tracing import configure_tracing

def create_app() -> Flask:
    container = Container()
    app = Flask(__name__)
    app.secret_key = config.secret
    app.container = container
    app.config["JWT_SECRET_KEY"] = config.secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=config.access_ttl)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(seconds=config.refresh_ttl)
    jwt = JWTManager(app)

    app.cli.add_command(superuser_cli)

    app.register_blueprint(users_api.bp)
    app.register_blueprint(roles_api.bp)
    app.register_blueprint(request_api.bp)

    app.config["SWAGGER"] = {"title": config.api_name, "uiversion": config.uiversion, "openapi": config.openapi}
    swag = Swagger(app, template=SWAGGER_TEMPLATE)
    configure_tracing(app)

    return app


if __name__ == "__main__":
    app = create_app()
    oauth.init_app(app)
    app.run(debug=True, threaded=False, port=8001)
