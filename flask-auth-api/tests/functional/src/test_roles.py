from http import HTTPStatus
from time import sleep

import pytest

from settings import config
from testdata.roles import role_data, update_role_data
from testdata.users import user_data

url_users = f"http://{config.api_ip}:{config.api_port}/api/v1/users"
url = f"http://{config.api_ip}:{config.api_port}/api/v1/roles"


@pytest.fixture
def insert_roles(make_post_request, prepare_user, make_superuser):
    async def inner():
        headers_access, _, uuid = await prepare_user(url_users, user_data[0][0])
        make_superuser(uuid)
        headers_access, _, uuid = await prepare_user(url_users, user_data[0][0])
        response = await make_post_request(url=f"{url}/", headers=headers_access, data=role_data)
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

    # get inserted roles
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    assert response.status == HTTPStatus.OK
    assert len(response.body) == len(role_data)


@pytest.mark.asyncio
async def test_create_roles_normal_user(make_post_request, clear_db_tables, clear_redis, prepare_user):

    # get access_token for normal user
    headers_access, _, _ = await prepare_user(url_users, user_data[0][0])

    # added roles by normal user
    response = await make_post_request(url=f"{url}/", headers=headers_access, data=role_data)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_roles_normal_user(make_get_request, clear_db_tables, clear_redis, prepare_user, insert_roles):

    response, _ = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get access_token for normal user
    headers_access, _, _ = await prepare_user(url_users, user_data[3][0])

    # get inserted roles
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_role(make_put_request, clear_db_tables, clear_redis, insert_roles, make_get_request):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # update role
    response = await make_put_request(url=f"{url}/{role_id}", headers=headers_access, data=update_role_data)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_update_role_normal_user(
    make_put_request, clear_db_tables, clear_redis, prepare_user, insert_roles, make_get_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get normal user access_token
    headers_access, _, _ = await prepare_user(url_users, user_data[3][0])

    # update role with normal user
    response = await make_put_request(url=f"{url}/{role_id}", headers=headers_access, data=update_role_data)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_role(make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # delete role
    response = await make_delete_request(url=f"{url}/{role_id}", headers=headers_access)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_delete_role_normal_user(
    make_delete_request, clear_db_tables, clear_redis, prepare_user, insert_roles, make_get_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get normal user access_token
    headers_access, _, _ = await prepare_user(url_users, user_data[3][0])

    # delete role by normnal usesr
    response = await make_delete_request(url=f"{url}/{role_id}", headers=headers_access)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_add_user_role(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get uuid for normal user to add role to
    _, _, uuid = await prepare_user(url_users, user_data[3][0])

    # add role to normal user by superuser
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_add_user_role_not_superuser(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get uuid for normal user to add role to and his access_token
    headers_access, _, uuid = await prepare_user(url_users, user_data[3][0])

    # add role to normal user by normal user
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_user_role(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get uuid for normal user to add role to
    _, _, uuid = await prepare_user(url_users, user_data[3][0])

    # add role by superuser to normal user
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK

    # delete role by superuser to normal user
    response = await make_delete_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_delete_user_role_not_superuser(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get uuid for normal user to add role to
    _, _, uuid = await prepare_user(url_users, user_data[3][0])

    # add role by superuser to normal user
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK

    # get access_token for normal user
    headers_access, _, uuid = await prepare_user(url_users, user_data[3][0])

    # delete role from normal user by normal user
    response = await make_delete_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_user_role_not_exist(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get uuid for normal user to add role to
    _, _, uuid = await prepare_user(url_users, user_data[3][0])

    # add role by superuser to normal user
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK

    # delete not exising role by superuser from normal user
    response = await make_delete_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": ["0774bba8-e050-40d0-a490-2a1c6fe33472"]})
    assert response.status == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_check_user_role(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    # create roles and get superuser access_token
    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get created role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]
    role_name = response.body[0]["role"]

    # get user UUID and refesh_token
    _, headers_refresh, uuid = await prepare_user(url_users, user_data[3][0])

    # add role to user with superuser
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK

    # check that user tokens are revoked after role added
    response = await make_get_request(url=f"{url_users}/refresh/{uuid}", headers=headers_refresh)
    assert response.status == HTTPStatus.UNAUTHORIZED

    # get new access_token for user - valid with new role included
    sleep(1)
    headers_access_user, _, _ = await prepare_user(url_users, user_data[3][0])

    # check newly generated user access_token by superuser
    response = await make_post_request(
        url=f"{url}/user/check",
        headers=headers_access,
        data={"access_token": headers_access_user["Authorization"].replace("Bearer ", "")},
    )
    assert response.status == HTTPStatus.OK
    assert response.body["role_id"][0] == role_name


@pytest.mark.asyncio
async def test_delete_role_assigned_to_user(
    make_delete_request, clear_db_tables, clear_redis, insert_roles, make_get_request, prepare_user, make_post_request
):

    # create roles and get superuser access_token
    response, headers_access = await insert_roles()
    assert response.status == HTTPStatus.CREATED

    # get created role_id
    response = await make_get_request(url=f"{url}/", headers=headers_access)
    role_id = response.body[0]["id"]

    # get user UUID and refesh_token
    _, headers_refresh, uuid = await prepare_user(url_users, user_data[3][0])

    # add role to user with superuser
    response = await make_post_request(url=f"{url}/user/{uuid}", headers=headers_access, data={"role_id": [role_id]})
    assert response.status == HTTPStatus.OK

    # delete by superuser role
    response = await make_delete_request(url=f"{url}/{role_id}", headers=headers_access)
    assert response.status == HTTPStatus.OK
