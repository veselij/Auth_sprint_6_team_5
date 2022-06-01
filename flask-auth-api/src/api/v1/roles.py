from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from flask.blueprints import Blueprint
from flask.helpers import make_response
from flask.json import jsonify
from flask.wrappers import Response

from api.v1.common_view import CustomSwaggerView
from containers.container import Container
from core.msg import Msg
from models.users_response_schemas import (
    CheckAccessTokenSchema,
    MsgSchema,
    RoleSchema,
    RoleUUIDSchema,
    UserRoleSchema,
    UserUUIDSchema,
)
from services.roles import RoleService
from services.users import UserService
from utils.exceptions import InvalidTokenError
from utils.view_decorators import jwt_verification, revoked_token_check

bp = Blueprint("roles", __name__, url_prefix="/api/v1/roles")


class Role(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification(superuser_only=True)]

    tags = ["roles"]

    requestBody = {
        "content": {
            "application/json": {
                "schema": {"type": "array", "items": RoleSchema},
                "example": [{"role": "role1", "description": "role description"}],
            },
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

    @inject
    def post(self, role_service: RoleService = Provide[Container.role_service]) -> Response:
        self.validate_body(RoleSchema, many=True)

        created = role_service.create_roles(self.validated_body)
        if not created:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.created.value)), HTTPStatus.CREATED.value)

    @inject
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

    @inject
    def delete(self, role_id: str, role_service: RoleService = Provide[Container.role_service]) -> Response:
        self.validate_path(RoleUUIDSchema)

        deleted = role_service.delete_role(role_id)
        if not deleted:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)

    @inject
    def put(self, role_id: str, role_service: RoleService = Provide[Container.role_service]) -> Response:
        self.validate_path(RoleUUIDSchema)
        self.validate_body(RoleSchema)

        updated = role_service.update_role(str(role_id), self.validated_body)
        if not updated:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)


class UserRoles(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification(superuser_only=True)]

    tags = ["roles"]

    requestBody = {
        "content": {
            "application/json": {"schema": UserRoleSchema, "example": {"role_id": []}},
        },
    }
    parameters = [
        {"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True},
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

    @inject
    def post(self, user_id: str, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_body(UserRoleSchema)

        created = user_service.add_user_roles(user_id, self.validated_body["role_id"])
        if not created:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)

    @inject
    def delete(self, user_id: str, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_body(UserRoleSchema)

        deleted = user_service.remove_user_roles(user_id, self.validated_body["role_id"])
        if not deleted:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)


class CheckUserRole(CustomSwaggerView):

    tags = ["roles"]

    requestBody = {
        "content": {
            "application/json": {"schema": CheckAccessTokenSchema, "example": {"access_token": ""}},
        },
    }

    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {"application/json": {"schema": UserRoleSchema, "example": Msg.ok.value}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
        HTTPStatus.FORBIDDEN.value: {
            "description": HTTPStatus.FORBIDDEN.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.forbidden.value}},
        },
    }

    @inject
    def post(self, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_body(CheckAccessTokenSchema)

        try:
            roles = user_service.check_user_roles(self.validated_body["access_token"])
        except InvalidTokenError:
            return make_response(jsonify(UserRoleSchema().load({"role_id": []})), HTTPStatus.OK.value)

        return make_response(jsonify(UserRoleSchema().load({"role_id": roles})), HTTPStatus.OK.value)


bp.add_url_rule("/", view_func=Role.as_view("role"), methods=["POST", "GET"])
bp.add_url_rule("/<uuid:role_id>", view_func=ModifyRole.as_view("modify_role"), methods=["PUT", "DELETE"])
bp.add_url_rule("/user/<uuid:user_id>", view_func=UserRoles.as_view("user_role"), methods=["POST", "DELETE"])
bp.add_url_rule("/user/check", view_func=CheckUserRole.as_view("check_role"), methods=["POST"])
