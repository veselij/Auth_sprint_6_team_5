import psycopg2
import pytest
from psycopg2.extras import DictCursor

from settings import config


@pytest.fixture(scope="function")
def clear_db_tables():
    connect = psycopg2.connect(
        dbname=config.pg_db,
        host=config.pg_host,
        port=config.pg_port,
        user=config.pg_user,
        password=config.pg_password,
        cursor_factory=DictCursor,
    )
    cur = connect.cursor()
    cur.execute(
        "DELETE from users_access_history;delete from user_roles;delete from roles;DELETE from social_account; delete from users"
    )
    cur.close()
    connect.commit()
    connect.close()


@pytest.fixture(scope="function")
def make_superuser():
    def inner(uuid: str):
        connect = psycopg2.connect(
            dbname=config.pg_db,
            host=config.pg_host,
            port=config.pg_port,
            user=config.pg_user,
            password=config.pg_password,
            cursor_factory=DictCursor,
        )
        cur = connect.cursor()
        cur.execute("update users set is_superuser=true where id='{0}';".format(uuid))
        cur.close()
        connect.commit()
        connect.close()

    return inner
