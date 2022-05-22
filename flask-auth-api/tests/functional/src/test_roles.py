from dataclasses import dataclass
from http import HTTPStatus
import pytest
import jwt

from settings import config
from testdata.users import user_data
from testdata.roles import role_data, update_role_data


url_users = f'http://{config.api_ip}:{config.api_port}/api/v1/users'
url = f'http://{config.api_ip}:{config.api_port}/api/v1/roles'


@pytest.fixture
def insert_roles(make_post_request, prepare_user, make_superuser):
    async def inner():
        headers_access, _, uuid = await prepare_user(url_users, user_data[0][0])
        make_superuser(uuid)
        headers_access, _, uuid = await prepare_user(url_users, user_data[0][0])
        response = await make_post_request(url=f'{url}/', headers=headers_access, data=role_data)
        return response, headers_access
    return inner


@pytest.mark.asyncio
async def test_create_roles(clear_db_tables, clear_redis, insert_roles):

    response, _ = await insert_roles()

    assert response.status == HTTPStatus.CREATED


@pytest.mark.asyncio
async def test_get_roles(make_get_request, clear_db_tables, clear_redis, insert_roles):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    response = await make_get_request(url=f'{url}/', headers=headers_access)
    assert response.status == HTTPStatus.OK
    assert len(response.body) == len(role_data)


@pytest.mark.asyncio
async def test_create_roles_normal_user(make_post_request, clear_db_tables, clear_redis, prepare_user):

    headers_access, _, _ = await prepare_user(url_users, user_data[0][0])
    response = await make_post_request(url=f'{url}/', headers=headers_access, data=role_data)

    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_roles_normal_user( make_get_request, clear_db_tables, clear_redis, prepare_user, insert_roles):

    response, _ = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    headers_access, _, _ = await prepare_user(url_users, user_data[3][0])

    response = await make_get_request(url=f'{url}/', headers=headers_access)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_role(make_put_request, clear_db_tables, clear_redis, insert_roles, make_get_request):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    response = await make_get_request(url=f'{url}/', headers=headers_access)
    role_id = response.body[0]['id']
    response = await make_put_request(url=f'{url}/{role_id}', headers=headers_access, data=update_role_data)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_update_role_normal_user(make_put_request, clear_db_tables, clear_redis, prepare_user, insert_roles, make_get_request):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED
    response = await make_get_request(url=f'{url}/', headers=headers_access)
    role_id = response.body[0]['id']

    headers_access, _, _ = await prepare_user(url_users, user_data[3][0])
    response = await make_put_request(url=f'{url}/{role_id}', headers=headers_access, data=update_role_data)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_role(make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request): 

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    response = await make_get_request(url=f'{url}/', headers=headers_access)
    role_id = response.body[0]['id']
    response = await make_delete_request(url=f'{url}/{role_id}', headers=headers_access)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_delete_role_normal_user(make_delete_request, clear_db_tables, clear_redis, prepare_user, insert_roles, make_get_request):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED
    response = await make_get_request(url=f'{url}/', headers=headers_access)
    role_id = response.body[0]['id']

    headers_access, _, _ = await prepare_user(url_users, user_data[3][0])
    response = await make_delete_request(url=f'{url}/{role_id}', headers=headers_access)
    assert response.status == HTTPStatus.UNAUTHORIZED
