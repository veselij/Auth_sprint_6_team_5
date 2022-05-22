from http import HTTPStatus
from typing import Type

from flasgger import SwaggerView
from flask import abort, jsonify, make_response, request
from marshmallow import ValidationError
from marshmallow.schema import Schema


class CustomSwaggerView(SwaggerView):

    consumes = []
    produces = []

    def validate_body(self, schema: Type[Schema], many: bool = False):
        try:
            body = schema(many=many).load(request.json)
        except ValidationError as err:
            abort(make_response(jsonify(err.messages), HTTPStatus.BAD_REQUEST.value))
        self.validated_body = body

    def validate_path(self, schema: Type[Schema], many: bool = False):
        try:
            path = schema(many=many).load(request.view_args)
        except ValidationError as err:
            abort(make_response(jsonify(err.messages), HTTPStatus.BAD_REQUEST.value))
        self.validated_path = path

    def validate_query(self, schema: Type[Schema], many: bool = False):
        try:
            query = schema(many=many).load(request.args.to_dict())
        except ValidationError as err:
            abort(make_response(jsonify(err.messages), HTTPStatus.BAD_REQUEST.value))
        self.validated_query = query
