from dataclasses import dataclass
from http import HTTPStatus

import jwt
import pyotp
import pytest
from settings import config
from testdata.users import update_user_data, user_data, user_login

url = f"http://{config.api_ip}:{config.api_port}/api/v1/users"
totp_url = f"http://{config.api_ip}:{config.api_port}/api/v1/totp"


@dataclass
class Header:
    header_access: dict
    header_refresh: dict
    uuid: str


async def check_tokens(response, func):
    refresh_token = response.body["refresh_token"]
    decoded_refresh_token = jwt.decode(refresh_token, options={"verify_signature": False})
    uuid = decoded_refresh_token["sub"]
    jti = decoded_refresh_token["jti"]
    uuid_redis = await func(jti)
    return uuid == uuid_redis


@pytest.mark.asyncio
@pytest.mark.parametrize("data,result,code", user_data)
async def test_register(data, result, code, make_post_request, clear_db_tables, clear_redis):

    # register user
    response = await make_post_request(url=f"{url}/register", data=data)

    assert response.status == code
    assert response.body == result


@pytest.mark.asyncio
@pytest.mark.parametrize("data,code", user_login)
async def test_login(data, code, make_post_request, clear_db_tables, get_from_redis, clear_redis):

    # login
    await make_post_request(url=f"{url}/register", data=user_data[0][0])
    response = await make_post_request(url=f"{url}/login", data=data)

    assert response.status == code


@pytest.mark.asyncio
async def test_refresh(make_get_request, clear_db_tables, clear_redis, get_from_redis, prepare_user):

    _, headers_refresh, uuid = await prepare_user(url, user_data[0][0])

    response = await make_get_request(url=f"{url}/refresh/{uuid}", headers=headers_refresh)

    assert response.status == HTTPStatus.OK
    assert await check_tokens(response, get_from_redis)


@pytest.mark.asyncio
async def test_logout(make_get_request, clear_db_tables, clear_redis, prepare_user):

    headers = []

    # login same user twice (aka 2 devices)
    for _ in range(2):
        headers_access, headers_refresh, uuid = await prepare_user(url, user_data[0][0])
        headers.append(Header(headers_access, headers_refresh, uuid))

    uuid = headers[0].uuid

    # logout only one user device
    response = await make_get_request(url=f"{url}/logout/{uuid}?all_devices=false", headers=headers[0].header_access)
    assert response.status == HTTPStatus.OK

    # check that only one device needs re-login
    for header, status in zip(headers, [HTTPStatus.UNAUTHORIZED, HTTPStatus.OK]):
        response = await make_get_request(url=f"{url}/history/{uuid}", headers=header.header_access)
        assert response.status == status

        response = await make_get_request(url=f"{url}/refresh/{uuid}", headers=header.header_refresh)
        assert response.status == status


@pytest.mark.asyncio
async def test_logout_all(make_get_request, clear_db_tables, clear_redis, prepare_user):

    headers = []

    # login same user twice (aka 2 devices)
    for _ in range(2):
        headers_access, headers_refresh, uuid = await prepare_user(url, user_data[0][0])
        headers.append(Header(headers_access, headers_refresh, uuid))

    uuid = headers[0].uuid

    # logout all user device
    response = await make_get_request(url=f"{url}/logout/{uuid}?all_devices=true", headers=headers[0].header_access)
    assert response.status == HTTPStatus.OK

    # check that all devices needs re-login
    for header in headers:
        response = await make_get_request(url=f"{url}/history/{uuid}", headers=header.header_access)
        assert response.status == HTTPStatus.UNAUTHORIZED

        response = await make_get_request(url=f"{url}/refresh/{uuid}", headers=header.header_refresh)
        assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_user_change(
    make_post_request, make_put_request, clear_db_tables, clear_redis, get_from_redis, prepare_user
):

    headers_access, _, uuid = await prepare_user(url, user_data[0][0])

    # update user
    response = await make_put_request(url=f"{url}/{uuid}", headers=headers_access, data=update_user_data)
    assert response.status == HTTPStatus.OK

    # check that login with new data - OK
    response = await make_post_request(url=f"{url}/login", data=update_user_data)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_user_history(make_get_request, clear_db_tables, clear_redis, prepare_user):

    headers_access, _, uuid = await prepare_user(url, user_data[0][0])

    response = await make_get_request(url=f"{url}/history/{uuid}?page_num=1&page_items=5", headers=headers_access)

    assert response.status == HTTPStatus.OK
    assert len(response.body) == 1


@pytest.mark.asyncio
async def test_superuser_change_normal_user(
    make_post_request, make_put_request, clear_db_tables, clear_redis, prepare_user, make_superuser, get_from_redis
):

    _, _, uuid_normal = await prepare_user(url, user_data[0][0])

    headers_access_super, _, uuid_super = await prepare_user(url, user_data[3][0])
    make_superuser(uuid_super)

    # relogin to get new access token with admin=1
    headers_access_super, _, uuid_super = await prepare_user(url, user_data[3][0])

    # superuser updates normal user
    response = await make_put_request(url=f"{url}/{uuid_normal}", headers=headers_access_super, data=update_user_data)
    assert response.status == HTTPStatus.OK

    # check that updated user login with new data - OK
    response = await make_post_request(url=f"{url}/login", data=update_user_data)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_normal_user_change_normal_user(
    make_post_request, make_put_request, clear_db_tables, clear_redis, prepare_user
):

    _, _, uuid_normal = await prepare_user(url, user_data[0][0])
    headers_access_normal2, _, _ = await prepare_user(url, user_data[3][0])

    # normal user change other normal user
    response = await make_put_request(url=f"{url}/{uuid_normal}", headers=headers_access_normal2, data=update_user_data)
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_register_social(make_get_request_no_body, clear_db_tables, clear_redis):

    # register yandex user
    response = await make_get_request_no_body(url=f"{url}/social/register/yandex")

    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_login_social_new_user(make_get_request, clear_db_tables, clear_redis, get_from_redis):

    # register yandex user
    response = await make_get_request(url=f"{url}/social/login/yandex")

    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_login_social_existing_user(make_get_request, clear_db_tables, clear_redis, get_from_redis):

    # register yandex user
    response = await make_get_request(url=f"{url}/social/login/yandex")

    assert response.status == HTTPStatus.OK

    # login after user created
    response = await make_get_request(url=f"{url}/social/login/yandex")

    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_delete_social_user_without_token(make_get_request, make_delete_request, clear_db_tables, clear_redis):

    # register yandex user
    response = await make_get_request(url=f"{url}/social/login/yandex")
    assert response.status == HTTPStatus.OK

    # delete yandex user
    response = await make_delete_request(url=f"{url}/social/delete/yandex")
    assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_social_user_with_token(
    make_get_request, make_delete_request, make_post_request, clear_db_tables, clear_redis
):

    # register yandex user
    response = await make_get_request(url=f"{url}/social/login/yandex")
    assert response.status == HTTPStatus.OK

    # prepare access token
    access_token = response.body["token"]["access_token"]
    headers_access = {"Authorization": f"Bearer {access_token}"}

    # delete yandex user
    response = await make_delete_request(url=f"{url}/social/delete/yandex", headers=headers_access)
    assert response.status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_add_totp(
    prepare_user, make_post_request, clear_db_tables, clear_redis, make_get_request, get_from_redis
):

    # register user and get token
    headers_access, headers_refresh, uuid = await prepare_user(url, user_data[0][0])

    # add totp
    response = await make_get_request(url=f"{totp_url}/sync", headers=headers_access)
    assert response.status == HTTPStatus.CREATED

    # prepare code
    uri = response.body["url"]
    p = pyotp.parse_uri(uri)
    code = str(p.now())

    # confirm code
    response = await make_post_request(url=f"{totp_url}/sync", headers=headers_access, data={"code": code})
    assert response.status == HTTPStatus.OK

    # login
    response = await make_post_request(url=f"{url}/login", data=user_data[0][0])
    assert response.status == HTTPStatus.OK
    request_id = response.body["request_id"]
    assert response.body["token"] == None

    response = await make_post_request(url=f"{totp_url}/check/{request_id}", data={"code": "123"})
    assert response.status == HTTPStatus.UNAUTHORIZED

    code = str(p.now())
    response = await make_post_request(url=f"{totp_url}/check/{request_id}", data={"code": code})
    assert response.status == HTTPStatus.CREATED
    assert response.body["access_token"] != None


@pytest.mark.asyncio
async def test_register_rate_limitter(make_post_request, clear_db_tables, clear_redis):

    # register user
    for _ in range(20):
        response = await make_post_request(url=f"{url}/register", data=user_data[0][0])
        assert response.status != HTTPStatus.TOO_MANY_REQUESTS
    response = await make_post_request(url=f"{url}/register", data=user_data[0][0])
    assert response.status == HTTPStatus.TOO_MANY_REQUESTS
