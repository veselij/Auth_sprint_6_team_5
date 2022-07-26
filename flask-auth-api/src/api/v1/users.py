from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, abort, jsonify, make_response, url_for, redirect
from flask.views import MethodView
from flask.wrappers import Response
from flask_jwt_extended import get_jti, get_jwt, jwt_required

from api.v1.common_view import CustomSwaggerView
from containers.container import Container
from core.msg import Msg
from models.users_response_schemas import (
    AllDevicesSchema,
    AuthSchema,
    DefaultPaginator,
    MsgSchema,
    ProvidersSchema,
    RequestIdSchema,
    TokenSchema,
    UserHistoryQuerySchema,
    UserHistorySchema,
    UserNotificationInfoSchema,
    UserUUIDSchema,
    UserVerificationQuerySchema,
)
from services.request import RequestService
from services.users import (
    BaseUserService,
    HistoryUserService,
    ManageSocialUserService,
    ManageUserService,
    RoleUserService,
)
from social.oauth import oauth
from social.providers import Providers
from social.userdata import user_data_registry
from utils.exceptions import (
    ConflictError,
    LoginPasswordError,
    ObjectDoesNotExistError,
    ProviderAuthTokenError,
)
from utils.rate_limit import rate_limiting
from utils.tracing import tracing
from utils.view_decorators import jwt_verification, revoked_token_check

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


class RegistrationView(CustomSwaggerView):
    decorators = [rate_limiting(), tracing]

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
        HTTPStatus.TOO_MANY_REQUESTS.value: {
            "description": HTTPStatus.TOO_MANY_REQUESTS.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.rate_limit.value}},
        },
    }

    @inject
    def post(self, user_service: ManageUserService = Provide[Container.manage_user_service]) -> Response:
        self.validate_body(AuthSchema)

        created = user_service.create_user(self.validated_body["login"], self.validated_body["password"])
        if not created:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        user_service.publish_user_created_event()
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
                "application/json": {"schema": RequestIdSchema},
            },
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    @inject
    def post(self, user_service: ManageUserService = Provide[Container.manage_user_service]) -> Response:
        self.validate_body(AuthSchema)

        try:
            request_id = user_service.autorize_user(self.validated_body["login"], self.validated_body["password"])
        except LoginPasswordError:
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value)
        return make_response(
            jsonify(RequestIdSchema().dump(request_id)),
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
    def get(
        self,
        user_id: UUID,
        request_service: RequestService = Provide[Container.request_service],
        user_service: BaseUserService = Provide[Container.base_user_service],
    ) -> Response:
        user = str(user_id)
        self.validate_path(UserUUIDSchema)

        token = get_jwt()
        if not request_service.check_refresh_token(token, user):
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value)
        return make_response(
            jsonify(
                TokenSchema().dump(
                    request_service.generate_tokens(user, token["admin"], user_service.get_user_roles(user))
                )
            ),
            HTTPStatus.OK.value,
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
    def get(self, user_id: str, user_service: BaseUserService = Provide[Container.base_user_service]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_query(AllDevicesSchema)

        if self.validated_query["all_devices"] == "true":
            user_service.revoke_access_token(user_id)
        else:
            jti = get_jwt()["jti"]
            user_service.revoke_access_token(user_id, jti)
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
    def put(self, user_id: str, user_service: ManageUserService = Provide[Container.manage_user_service]) -> Response:
        self.validate_body(AuthSchema)
        self.validate_path(UserUUIDSchema)

        user = user_service.get_user(user_id)
        if not user:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        try:
            user_service.update_user_data(user, self.validated_body)
        except ConflictError:
            return make_response(jsonify(MsgSchema().load(Msg.alredy_exists.value)), HTTPStatus.CONFLICT.value)
        return make_response(jsonify(MsgSchema().load(Msg.ok.value)), HTTPStatus.OK.value)

    @inject
    def get(self, user_id: str, user_service: ManageUserService = Provide[Container.manage_user_service]) -> Response:
        self.validate_body(AuthSchema)
        self.validate_path(UserUUIDSchema)

        user = user_service.get_user(user_id)
        if not user:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)
        return make_response(jsonify(UserNotificationInfoSchema(many=True).dump(user)), HTTPStatus.OK.value)


class UserVerificationView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_verification()]

    tags = ['users']
    parameters = [
        {"in": "path", "name": "user_id", "schema": {"type": "string", "format": "uuid"}, "required": True},
        {"in": "query", "name": "expired", "schema": {"type": "string", "format": "datetime"}, "required": True},
        {"in": "query", "name": "redirect_url", "schema": {"type": "string"}, "required": True},
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
    def get(self, user_id: str, user_service: ManageUserService = Provide[Container.manage_user_service ]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_query(UserVerificationQuerySchema)
        user = user_service.get_user(user_id)
        expired = datetime.fromisoformat(self.validated_query['expired'])
        if datetime.now(timezone(timedelta(hours=user.timezone))) >= expired:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)
        return redirect(self.validated_query['redirect_url'], HTTPStatus.OK.value, Response=None)


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
        {
            "in": "query",
            "name": "year",
            "schema": {
                "type": "integer",
                "default": datetime.now().year,
            },
        },
        {
            "in": "query",
            "name": "month",
            "schema": {
                "type": "integer",
                "minimum": 1,
                "maximum": 12,
                "default": datetime.now().month,
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
    def get(self, user_id: str, user_service: HistoryUserService = Provide[Container.history_user_service ]) -> Response:
        self.validate_path(UserUUIDSchema)
        self.validate_query(UserHistoryQuerySchema)

        user_history = user_service.get_user_history(
            user_id,
            self.validated_query.get("page_num", DefaultPaginator.page_num.value),
            self.validated_query.get("page_items", DefaultPaginator.page_items.value),
            self.validated_query.get("year", datetime.now().year),
            self.validated_query.get("month", datetime.now().month),
        )
        if not user_history:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        return make_response(jsonify(UserHistorySchema(many=True).dump(user_history)), HTTPStatus.OK.value)


class SocialLoginView(CustomSwaggerView):

    tags = ["users"]

    parameters = [
        {
            "in": "path",
            "name": "provider",
            "schema": {"type": "string", "enum": [field.name for field in Providers]},
            "required": True,
        },
    ]
    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {"application/json": {"schema": RequestIdSchema}},
        },
        HTTPStatus.NOT_FOUND.value: {
            "description": HTTPStatus.NOT_FOUND.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.not_found.value}},
        },
    }

    @inject
    def get(self, provider: str, user_service: ManageSocialUserService = Provide[Container.manage_social_user_service ]) -> Response:
        self.validate_path(ProvidersSchema)
        client = oauth.create_client(provider)

        if not client:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        token = client.authorize_access_token()
        try:
            user_data = user_data_registry[provider](token, client)
        except ProviderAuthTokenError:
            return make_response(jsonify(MsgSchema().load(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value)

        try:
            request_id = user_service.login_via_social_provider(user_data)
        except (ObjectDoesNotExistError, ConflictError):
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        return make_response(
            jsonify(RequestIdSchema().dump(request_id)),
            HTTPStatus.OK.value,
        )


class SocialRegisterView(MethodView):
    def get(self, provider: str) -> None:
        client = oauth.create_client(provider)
        if not client:
            abort(404)

        redirect_uri = url_for("users.social", provider=provider, _external=True)
        return client.authorize_redirect(redirect_uri)


class DeleteSocialAccountView(CustomSwaggerView):
    decorators = [revoked_token_check(), jwt_required()]

    tags = ["users"]

    parameters = [
        {
            "in": "path",
            "name": "provider",
            "schema": {"type": "string", "enum": [field.name for field in Providers]},
            "required": True,
        },
    ]
    responses = {
        HTTPStatus.OK.value: {
            "description": HTTPStatus.OK.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.ok.value}},
        },
        HTTPStatus.NOT_FOUND.value: {
            "description": HTTPStatus.NOT_FOUND.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.not_found.value}},
        },
        HTTPStatus.UNAUTHORIZED.value: {
            "description": HTTPStatus.UNAUTHORIZED.phrase,
            "content": {"application/json": {"schema": MsgSchema, "example": Msg.unauthorized.value}},
        },
    }

    @inject
    def delete(self, provider: str, user_service: ManageSocialUserService = Provide[Container.manage_social_user_service]) -> Response:
        self.validate_path(ProvidersSchema)

        token = get_jwt()

        try:
            user_service.delete_social_account(token, provider)
        except ObjectDoesNotExistError:
            return make_response(jsonify(MsgSchema().load(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value)

        return make_response(
            jsonify(MsgSchema().load(Msg.ok.value)),
            HTTPStatus.OK.value,
        )


bp.add_url_rule("/<uuid:user_id>", view_func=ChangeUserView.as_view("change_user"), methods=["PUT", "GET"])
bp.add_url_rule("/register", view_func=RegistrationView.as_view("register"), methods=["POST"])
bp.add_url_rule(
    "/social/delete/<string:provider>", view_func=DeleteSocialAccountView.as_view("social_delete"), methods=["DELETE"]
)
bp.add_url_rule("/social/login/<string:provider>", view_func=SocialLoginView.as_view("social"), methods=["GET"])
bp.add_url_rule(
    "/social/register/<string:provider>", view_func=SocialRegisterView.as_view("social_register"), methods=["GET"]
)
bp.add_url_rule("/login", view_func=LoginView.as_view("login"), methods=["POST"])
bp.add_url_rule("/refresh/<uuid:user_id>", view_func=RefreshView.as_view("refresh"), methods=["GET"])
bp.add_url_rule("/logout/<uuid:user_id>", view_func=LogoutView.as_view("logout"), methods=["GET"])
bp.add_url_rule("/history/<uuid:user_id>", view_func=UserHistoryView.as_view("history"), methods=["GET"])
bp.add_url_rule("/verificate/<uuid:user_id>", view_func=UserVerificationView.as_view("verification"), methods=["GET"])
