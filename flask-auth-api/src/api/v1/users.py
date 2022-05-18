from http import HTTPStatus
from typing import Type
from uuid import UUID

from flasgger import SwaggerView
from flask import Blueprint, abort, jsonify, make_response, request
from flask_jwt_extended import get_jwt
from marshmallow import ValidationError
from marshmallow.schema import Schema

from api.v1.users_schemas import (
    AllDevicesSchema,
    AuthSchema,
    DefaultPaginator,
    MsgSchema,
    PaginationSchema,
    TokenSchema,
    UserHistorySchema,
    UserUUIDSchema,
)
from db.cache import get_cache_access, get_cache_refresh
from models.db_models import get_user_by_id
from services.decorators import jwt_verification, revoked_token_check
from services.users import (
    autorize_user,
    check_refresh_token,
    create_user,
    generate_tokens,
    get_user_history,
    revoke_access_token,
    update_user_data,
)

bp = Blueprint("users", __name__, url_prefix="/users")


class CustomSwaggerView(SwaggerView):

    consumes = []
    produces = []

    def validate_body(self, schema: Type[Schema]):
        try:
            body = schema().load(request.json)
        except ValidationError as err:
            abort(make_response(jsonify(err.messages), HTTPStatus.BAD_REQUEST.value))
        self.validated_body = body

    def validate_path(self, schema: Type[Schema]):
        try:
            path = schema().load(request.view_args)
        except ValidationError as err:
            abort(make_response(jsonify(err.messages), HTTPStatus.BAD_REQUEST.value))
        self.validated_path = path

    def validate_query(self, schema: Type[Schema]):
        try:
            query = schema().load(request.args.to_dict())
        except ValidationError as err:
            abort(make_response(jsonify(err.messages), HTTPStatus.BAD_REQUEST.value))
        self.validated_query = query


class RegistrationView(CustomSwaggerView):

    tags = ["users"]
    requestBody = {
        "content": {
            "application/json": {"schema": AuthSchema, "example": {"login": "admin123", "password": "admin123"}},
        },
    }
    responses = {
        HTTPStatus.CREATED.value: {"description": HTTPStatus.CREATED.phrase},
        HTTPStatus.BAD_REQUEST.value: {
            "description": HTTPStatus.BAD_REQUEST.phrase,
            "content": {"application/json": {"schema": MsgSchema}},
        },
        HTTPStatus.CONFLICT.value: {
            "description": HTTPStatus.CONFLICT.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "User already exists"}}},
        },
    }

    def post(self):
        self.validate_body(AuthSchema)
        user = create_user(self.validated_body["login"], self.validated_body["password"])
        if not user:
            return jsonify({"msg": "User already exists"}), HTTPStatus.CONFLICT.value
        return "", HTTPStatus.CREATED.value


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
                "application/json": {"schema": TokenSchema, "example": {"access_token": "111", "refresh_token": "222"}},
            },
        },
        HTTPStatus.BAD_REQUEST.value: {
            "description": HTTPStatus.BAD_REQUEST.phrase,
            "content": {"application/json": {"schema": MsgSchema}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "Wrong login or password"}}},
        },
    }

    def post(self):
        self.validate_body(AuthSchema)
        user = autorize_user(self.validated_body["login"], self.validated_body["password"])
        if not user:
            return jsonify({"msg": "Wrong login or password"}), HTTPStatus.UNAUTHORIZED.value
        return jsonify(**generate_tokens(str(user.id), get_cache_refresh())), HTTPStatus.OK.value


class RefreshView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification()]

    tags = ["users"]

    parameters = [{"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True}]
    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {
                "application/json": {"schema": TokenSchema, "example": {"access_token": "111", "refresh_token": "222"}},
            },
        },
        HTTPStatus.BAD_REQUEST.value: {
            "description": HTTPStatus.BAD_REQUEST.phrase,
            "content": {"application/json": {"schema": MsgSchema}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "Missing Authorization Header"}}},
        },
    }

    def post(self, user_id: UUID):
        user = str(user_id)
        self.validate_path(UserUUIDSchema)
        token = get_jwt()
        if not check_refresh_token(token, get_cache_refresh(), user):
            return jsonify({"msg": "Wrong login or password"}), HTTPStatus.UNAUTHORIZED.value

        return jsonify(**generate_tokens(user, get_cache_refresh())), HTTPStatus.OK.value


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
        },
        HTTPStatus.BAD_REQUEST.value: {
            "description": HTTPStatus.BAD_REQUEST.phrase,
            "content": {"application/json": {"schema": MsgSchema}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "Missing Authorization Header"}}},
        },
    }

    def post(self, user_id: str):
        self.validate_path(UserUUIDSchema)
        self.validate_query(AllDevicesSchema)
        token = get_jwt()
        revoke_access_token(token, get_cache_access(), user_id, self.validated_query["all_devices"])
        return "", HTTPStatus.OK.value


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
        },
        HTTPStatus.BAD_REQUEST.value: {
            "description": HTTPStatus.BAD_REQUEST.phrase,
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "Missing Authorization Header"}}},
        },
        HTTPStatus.NOT_FOUND.value: {
            "description": HTTPStatus.NOT_FOUND.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "User does not exist"}}},
        },
        HTTPStatus.CONFLICT.value: {
            "description": HTTPStatus.CONFLICT.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "Login already exists"}}},
        },
    }

    def put(self, user_id: str):
        self.validate_body(AuthSchema)
        self.validate_path(UserUUIDSchema)

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"msg": "User does not exist"}), HTTPStatus.NOT_FOUND.value

        if not update_user_data(user, self.validated_body["login"], self.validated_body["password"]):
            return jsonify({"msg": "Login already exists"}), HTTPStatus.CONFLICT.value
        return "", HTTPStatus.OK.value


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
        HTTPStatus.BAD_REQUEST.value: {
            "description": HTTPStatus.BAD_REQUEST.phrase,
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "Missing Authorization Header"}}},
        },
        HTTPStatus.NOT_FOUND.value: {
            "description": HTTPStatus.NOT_FOUND.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": {"msg": "User does not exist"}}},
        },
    }

    def get(self, user_id: str):
        self.validate_path(UserUUIDSchema)
        self.validate_query(PaginationSchema)

        user_history = get_user_history(
            user_id,
            UserHistorySchema,
            self.validated_query.get("page_num", DefaultPaginator.page_num.value),
            self.validated_query.get("page_items", DefaultPaginator.page_items.value),
        )
        if not user_history:
            return jsonify({"msg": "History does not exist"}), HTTPStatus.NOT_FOUND.value

        return jsonify(user_history), HTTPStatus.OK.value


bp.add_url_rule("/<uuid:user_id>", view_func=ChangeUserView.as_view("change_user"), methods=["PUT"])
bp.add_url_rule("/register", view_func=RegistrationView.as_view("register"), methods=["POST"])
bp.add_url_rule("/login", view_func=LoginView.as_view("login"), methods=["POST"])
bp.add_url_rule("/refresh/<uuid:user_id>", view_func=RefreshView.as_view("refresh"), methods=["POST"])
bp.add_url_rule("/logout/<uuid:user_id>", view_func=LogoutView.as_view("logout"), methods=["POST"])
bp.add_url_rule("/history/<uuid:user_id>", view_func=UserHistoryView.as_view("history"), methods=["GET"])
