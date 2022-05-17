from flasgger import SwaggerView
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from api.v1.users_schemas import AuthSchema, MsgSchema, TokenSchema
from db.cache import get_cache_refresh, get_cache_access
from services.users import autorize_user, create_user, generate_tokens, check_refresh_token, check_revoked_token
from services.decorators import jwt_verification

bp = Blueprint('users', __name__, url_prefix='/users')


class RegistrationView(SwaggerView):

    tags = ['users']
    consumes = []
    produces = []
    requestBody = {
        'content': {
            'application/json': {'schema': AuthSchema, 'example': {'login': 'admin123', 'password': 'admin123'}},
        },
    }
    responses = {
        201: {'description': 'User created successfully'},
        400: {
            'description': 'Bad request',
            'content': {'application/json': {'schema': MsgSchema, 'example': {'msg': 'Missing login or password'}}},
        },
        409: {
            'description': 'Conflict',
            'content': {'application/json': {'schema': MsgSchema, 'example': {'msg': 'User already exists'}}},
        },
    }
    validation = True

    def post(self):
        login = request.json.get('login', None)
        password = request.json.get('password', None)
        if not login or not password:
            return jsonify({'msg': 'Missing login or password'}), 400
        user = create_user(login, password)
        if not user:
            return jsonify({'msg': 'User already exists'}), 409
        return '', 201


class LoginView(SwaggerView):

    tags = ['users']
    consumes = []
    produces = []
    requestBody = {
        'content': {
            'application/json': {'schema': AuthSchema, 'example': {'login': 'admin123', 'password': 'admin123'}},
        },
    }
    responses = {
        200: {
            'description': 'User logged successfully',
            'content': {
                'application/json': {'schema': TokenSchema, 'example': {'access_token': '111', 'refresh_token': '222'}},
            },
        },
        401: {
            'description': 'Unauthorized',
            'content': {'application/json': {'schema': MsgSchema, 'example': {'msg': 'Wrong login or password'}}},
        },
    }
    validation = True

    def post(self):
        login = request.json.get('login', None)
        password = request.json.get('password', None)

        user = autorize_user(login, password)
        if not user:
            return jsonify({'msg': 'Wrong login or password'}), 401
        return jsonify(**generate_tokens(str(user.id), get_cache_refresh()))


class RefreshView(SwaggerView):
    decorators = [jwt_verification()]

    tags = ['users']

    parameters = [{"in": "path", "name": "user_id",  "schema": {"type": "string", "format": "uuid"}, "required": True}]
    consumes = []
    produces = []
    responses = {
        200: {
            'description': 'Token refreshed successfully',
            'content': {
                'application/json': {'schema': TokenSchema, 'example': {'access_token': '111', 'refresh_token': '222'}},
            },
        },
        401: {
            'description': 'Unauthorized',
            'content': {'application/json': {'schema': MsgSchema, 'example': {'msg': 'Missing Authorization Header'}}},
        },
    }

    def post(self, user_id):
        token = get_jwt()
        user_id = check_refresh_token(token, get_cache_refresh())

        if not user_id or not check_revoked_token(user_id, get_cache_access(), token):
            return jsonify({'msg': 'Wrong login or password'}), 401

        return jsonify(**generate_tokens(user_id, get_cache_refresh()))


bp.add_url_rule('/register', view_func=RegistrationView.as_view('register'), methods=['POST'])
bp.add_url_rule('/login', view_func=LoginView.as_view('login'), methods=['POST'])
bp.add_url_rule('/refresh/<uuid:user_id>', view_func=RefreshView.as_view('refresh'), methods=['POST'])
