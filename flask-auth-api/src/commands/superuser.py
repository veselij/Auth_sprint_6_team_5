from getpass import getpass
from typing import Optional

import click
from flask.cli import AppGroup

from core.config import config
from db.db import Database
from models.db_models import User
from utils.password_hashing import get_password_hash
from repository.repository import Repositiry

superuser_cli = AppGroup("superuser")


db = Database()
repository = Repositiry(db.session_manager)

class InvalidUserDataError(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


def read_password(prompt: str) -> str:
    password: Optional[str] = None
    while not password:
        password = getpass(prompt=prompt)
    return password


def get_password():
    password: str = read_password(prompt="Password:")
    password2: str = read_password(prompt="Please confirm password:")
    while password != password2:
        print("Passwords did not match")
        password = read_password(prompt="Password:")
        password2 = read_password(prompt="Please confirm password:")
    return password


def read_name(prompt: str) -> str:
    name: Optional[str] = None
    while not name:
        name = input(prompt)
    return name


def create_superuser_int():
    name: str
    password: str

    name = read_name("Please specify superuser name: ")
    while repository.get_object_by_field(User, login=name):
        print("Username {0} already exists".format(name))
        name = read_name("Please specify superuser name: ")

    password = get_password()

    user = User(login=name, password=get_password_hash(password), is_superuser=True)

    repository.create_obj_in_db(user)


def create_superuser():
    name: Optional[str] = config.superuser
    password: Optional[str] = config.superuser_password

    if not name or not password:
        raise InvalidUserDataError("password or name not specified")
    if repository.get_object_by_field(User, login=name):
        raise InvalidUserDataError("user already exisit")

    user = User(login=name, password=get_password_hash(password), is_superuser=True)
    repository.create_obj_in_db(user)


@superuser_cli.command("create")
@click.option(
    "--interactive/--no-interactive",
    show_default=True,
    default=True,
    help="If True interactive prompt will be used, if False Username and password will be loaded from env variables",
)
def create_superuser_command(interactive):
    if interactive:
        create_superuser_int()
    else:
        create_superuser()


@superuser_cli.command("reset-password")
@click.argument("login")
def reset_password(login):
    user = repository.get_object_by_field(User, login=login)
    if not user:
        raise InvalidUserDataError("User {0} does not exists".format(login))
    password: str = get_password()
    password_hash = get_password_hash(password)
    repository.update_obj_in_db(User, {"password": password_hash}, login=login)
