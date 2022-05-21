from http import HTTPStatus


user_data = (
    (
    {"login": "user1", "password": "password1"},
    {'msg': 'User successfully created'},
    HTTPStatus.CREATED,
    ),
    (
    {"password": "password1"},
    {
      "login": [
        "Missing data for required field."
      ]
    },
    HTTPStatus.BAD_REQUEST,
    ),
    (
        {"login":"user1", "password": "password1", "name": "vasy"},
    {  
        "name": [
        "Unknown field."
          ]
    },
    HTTPStatus.BAD_REQUEST,
    ),
    (
    {"login": "super", "password": "password1"},
    {'msg': 'User successfully created'},
    HTTPStatus.CREATED,
    ),
)

user_login = (
    (
    user_data[0][0],
    HTTPStatus.OK,
    ),
    (
    {"login": "user1", "password": "password2"},
    HTTPStatus.UNAUTHORIZED,
    ),
)
update_user_data = {"login": "user2", "password": "password2"}
