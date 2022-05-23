from http import HTTPStatus
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, jsonify, make_response
from flask.wrappers import Response
from flask_jwt_extended import get_jwt

from api.v1.common_view import CustomSwaggerView
from containers.container import Container
from core.msg import Msg
from models.users_response_schemas import (
    AllDevicesSchema,
    AuthSchema,
    DefaultPaginator,
    MsgSchema,
    PaginationSchema,
    TokenSchema,
    UserHistorySchema,
    UserUUIDSchema,
)
from services.users import UserService
from utils.view_decorators import jwt_verification, revoked_token_check

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


class RegistrationView(CustomSwaggerView):

    tags = ["users"]
    requestBody = {
        "content": {
            "application/json": {"schema": AuthSchema, "example": {"login": "admin123", "password": "admin123"}},
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
    }

    @inject
    def post(self, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_body(AuthSchema)

        created = user_service.create_user(self.validated_body["login"], self.validated_body["password"])
        if not created:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.created.value)), HTTPStatus.CREATED.value)


class LoginView(CustomSwaggerView):

    tags = ["users"]
    requestBody = {
        "content": {
            "application/json": {"schema": AuthSchema, "example": {"login": "admin123", "password": "admin123"}},
        },
    }
    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {
                "application/json": {"schema": TokenSchema},
            },
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    @inject
    def post(self, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_body(AuthSchema)

        user = user_service.autorize_user(self.validated_body["login"], self.validated_body["password"])
        if not user:
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value)
        return make_response(
            jsonify(TokenSchema().load(user_service.generate_tokens(str(user.id), user.is_superuser))),
            HTTPStatus.OK.value,
        )


class RefreshView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification()]

    tags = ["users"]

    parameters = [{"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True}]
    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {
                "application/json": {"schema": TokenSchema},
            },
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    @inject
    def get(self, user_id: UUID, user_service: UserService = Provide[Container.user_service]) -> Response:
        user = str(user_id)
        self.validate_path(UserUUIDSchema)

        token = get_jwt()
        if not user_service.check_refresh_token(token, user):
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value)
        return make_response(
            jsonify(TokenSchema().load(user_service.generate_tokens(user, token["admin"]))), HTTPStatus.OK.value,
        )


class LogoutView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification()]

    tags = ["users"]

    parameters = [
        {"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True},
        {"in": "query", "name": "all_devices", "schema": {"type": "string", "enum": ["false", "true"]}},
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
    }

    @inject
    def get(self, user_id: str, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_query(AllDevicesSchema)

        token = get_jwt()
        user_service.revoke_access_token(token, user_id, self.validated_query["all_devices"])
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)


class ChangeUserView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification()]

    tags = ["users"]
    parameters = [{"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True}]
    requestBody = {
        "content": {
            "application/json": {"schema": AuthSchema, "example": {"login": "admin123", "password": "admin123"}},
        },
    }
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
        HTTPStatus.CONFLICT.value: {
            "description": HTTPStatus.CONFLICT.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.alredy_exists.value}},
        },
    }

    @inject
    def put(self, user_id: str, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_body(AuthSchema)
        self.validate_path(UserUUIDSchema)

        user = user_service.get_user(user_id)
        if not user:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        if not user_service.update_user_data(user, self.validated_body):
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)


class UserHistoryView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification()]

    tags = ["users"]
    parameters = [
        {"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True},
        {
            "in": "query",
            "name": "page_num",
            "schema": {
                "type": "integer",
                "minimum": DefaultPaginator.min_page_num.value,
                "maximum": DefaultPaginator.min_page_num.value,
                "default": DefaultPaginator.page_num.value,
            },
        },
        {
            "in": "query",
            "name": "page_items",
            "schema": {
                "type": "integer",
                "minimum": DefaultPaginator.min_page_items.value,
                "maximum": DefaultPaginator.max_page_items.value,
                "default": DefaultPaginator.page_items.value,
            },
        },
    ]

    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {
                "application/json": {"schema": {"type": "array", "items": UserHistorySchema}},
            },
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
    def get(self, user_id: str, user_service: UserService = Provide[Container.user_service]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_query(PaginationSchema)

        user_history = user_service.get_user_history(
            user_id,
            self.validated_query.get("page_num", DefaultPaginator.page_num.value),
            self.validated_query.get("page_items", DefaultPaginator.page_items.value),
        )
        if not user_history:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        return make_response(jsonify(UserHistorySchema(many=True).dump(user_history)), HTTPStatus.OK.value)


bp.add_url_rule("/<uuid:user_id>", view_func=ChangeUserView.as_view("change_user"), methods=["PUT"])
bp.add_url_rule("/register", view_func=RegistrationView.as_view("register"), methods=["POST"])
bp.add_url_rule("/login", view_func=LoginView.as_view("login"), methods=["POST"])
bp.add_url_rule("/refresh/<uuid:user_id>", view_func=RefreshView.as_view("refresh"), methods=["GET"])
bp.add_url_rule("/logout/<uuid:user_id>", view_func=LogoutView.as_view("logout"), methods=["GET"])
bp.add_url_rule("/history/<uuid:user_id>", view_func=UserHistoryView.as_view("history"), methods=["GET"])
