from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from flask.blueprints import Blueprint
from flask.helpers import make_response
from flask.json import jsonify
from flask.wrappers import Response
from flask_jwt_extended.utils import get_jwt
from flask_jwt_extended.view_decorators import jwt_required

from api.v1.common_view import CustomSwaggerView
from containers.container import Container
from core.msg import Msg
from models.users_response_schemas import (
    MsgSchema,
    ProvisioningUrlSchema,
    RequestSchema,
    SocialTokenSchema,
    TotpCodeSchema,
)
from services.request import RequestService
from utils.exceptions import ObjectDoesNotExistError, TotpNotSyncError
from utils.view_decorators import revoked_token_check

bp = Blueprint("totp", __name__, url_prefix="/api/v1/totp")


class TotpSync(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_required()]

    tags = ["totp"]

    requestBody = {
        "content": {
            "application/json": {"schema": TotpCodeSchema, "example": {"code": "1234"}},
        },
    }

    responses = {
        HTTPStatus.CREATED.value: {
            "description": HTTPStatus.CREATED.phrase,
            "content": {
                "application/json": {"schema": ProvisioningUrlSchema},
            },
        },
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.ok.value}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    @inject
    def get(self, request_service: RequestService = Provide[Container.request_service]) -> Response:

        token = get_jwt()

        provisioning_url = request_service.generate_provisioning_url(token)
        return make_response(jsonify(ProvisioningUrlSchema().dump(provisioning_url)), HTTPStatus.CREATED.value)

    @inject
    def post(self, request_service: RequestService = Provide[Container.request_service]) -> Response:
        self.validate_body(TotpCodeSchema)

        token = get_jwt()

        try:
            token = request_service.activate_totp(token, self.validated_body["code"])
        except ObjectDoesNotExistError:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)


class TotpCheck(CustomSwaggerView):

    tags = ["totp"]

    parameters = [{"in": "path", "name": "request_id", "schema": {"type": "string"}, "required": True}]

    requestBody = {
        "content": {
            "application/json": {"schema": TotpCodeSchema, "example": {"code": "1234"}},
        },
    }

    responses = {
        HTTPStatus.CREATED.value: {
            "description": HTTPStatus.CREATED.phrase,
            "content": {
                "application/json": {"schema": SocialTokenSchema},
            },
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    @inject
    def post(self, request_id: str, request_service: RequestService = Provide[Container.request_service]) -> Response:
        self.validate_body(TotpCodeSchema)
        self.validate_path(RequestSchema)

        try:
            token = request_service.check_totp(request_id, self.validated_body["code"])
        except ObjectDoesNotExistError:
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value)
        except TotpNotSyncError:
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized_totp.value)), HTTPStatus.UNAUTHORIZED.value)

        return make_response(jsonify(SocialTokenSchema().dump(token)), HTTPStatus.CREATED.value)


bp.add_url_rule("/check/<string:request_id>", view_func=TotpCheck.as_view("totp_check"), methods=["POST"])
bp.add_url_rule("/sync", view_func=TotpSync.as_view("totp_sync"), methods=["GET", "POST"])
