
from http import HTTPStatus
from uuid import UUID
from dependency_injector.wiring import Provide
from flask.blueprints import Blueprint
from flask.helpers import make_response
from flask.json import jsonify
from flask.wrappers import Response

from api.v1.common_view import CustomSwaggerView
from core.msg import Msg
from models.users_response_schemas import MsgSchema, RoleSchema, RoleUUIDSchema
from services.roles import RoleService
from utils.view_decorators import jwt_verification, revoked_token_check
from services.roles import RoleService
from containers.container import Container


bp = Blueprint("roles", __name__, url_prefix="/api/v1/roles")


class Role(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification(superuser_only=True)]

    tags = ["roles"]

    requestBody = {
        "content": {
            "application/json": {"schema": {"type": "array", "items": RoleSchema}, "example": [{"role": "role1", "description": "role description"}]},
        },
    }

    responses = {
        HTTPStatus.CREATED.value: {
            "description": HTTPStatus.CREATED.phrase,
            "content": {
                "application/json": {"schema": MsgSchema, "example": Msg.created.value},
            },
        },
        HTTPStatus.CONFLICT.value: {
            "description": HTTPStatus.CONFLICT.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.alredy_exists.value}},
        },
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {
                "application/json": {"schema": {"type": "array", "items": RoleSchema}},
            },
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    def post(self, role_service: RoleService = Provide[Container.role_service]) -> Response:
        self.validate_body(RoleSchema, many=True)

        created = role_service.create_roles(self.validated_body)
        if not created:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.created.value)), HTTPStatus.CREATED.value)



    def get(self, role_service: RoleService = Provide[Container.role_service]) -> Response:

        roles = role_service.get_roles()
        if not roles:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)
        return make_response(jsonify(RoleSchema(many=True).dump(roles)), HTTPStatus.OK.value)


class ModifyRole(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification(superuser_only=True)]

    tags = ["roles"]

    requestBody = {
        "content": {
            "application/json": {"schema": RoleSchema, "example": {"role": "role1", "description": "role description"}},
        },
    }
    parameters = [
        {"in": "path", "name": "role_id", "schema": {"type": "string", "format": "uuid"}, "required": True},
    ]



    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.ok.value}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
        HTTPStatus.NOT_FOUND.value: {
            "description": HTTPStatus.NOT_FOUND.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.not_found.value}},
        },
    }

    def delete(self, role_id: str, role_service: RoleService = Provide[Container.role_service]) -> Response:
        self.validate_path(RoleUUIDSchema)

        deleted = role_service.delete_role(role_id)
        if not deleted:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)

    def put(self, role_id: str, role_service: RoleService = Provide[Container.role_service]) -> Response:
        self.validate_path(RoleUUIDSchema)
        self.validate_body(RoleSchema)

        updated = role_service.update_role(str(role_id), self.validated_body)
        if not updated:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)


bp.add_url_rule("/", view_func=Role.as_view("role"), methods=["POST", "GET"])
bp.add_url_rule("/<uuid:role_id>", view_func=ModifyRole.as_view("modify_role"), methods=["PUT", "DELETE"])
