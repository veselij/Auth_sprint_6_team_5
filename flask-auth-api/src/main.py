from datetime import timedelta

from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager

import api.v1.users as users_api
import api.v1.roles as roles_api
from commands.superuser import superuser_cli
from core.config import config, SWAGGER_TEMPLATE
from containers.container import Container


def create_app() -> Flask:
    container = Container()
    app = Flask(__name__)
    app.container = container

    app.config["JWT_SECRET_KEY"] = config.secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=config.access_ttl)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(seconds=config.refresh_ttl)
    jwt = JWTManager(app)


    app.cli.add_command(superuser_cli)

    app.register_blueprint(users_api.bp)
    app.register_blueprint(roles_api.bp)

    app.config["SWAGGER"] = {"title": config.api_name, "uiversion": config.uiversion, "openapi": config.openapi}
    swag = Swagger(app, template=SWAGGER_TEMPLATE)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, threaded=False, port=8000)
