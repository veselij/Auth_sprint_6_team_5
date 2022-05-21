from dataclasses import dataclass
from http import HTTPStatus
import pytest
import jwt

from settings import config
from testdata.users import user_data, user_login, update_user_data



url = f'http://{config.api_ip}:{config.api_port}/users'


@dataclass
class Header:
    header_access: dict
    header_refresh: dict
    uuid: str


async def check_tokens(response, func):
    refresh_token = response.body['refresh_token']
    decoded_refresh_token = jwt.decode(refresh_token, options={"verify_signature": False})
    uuid = decoded_refresh_token['sub']
    jti = decoded_refresh_token['jti']
    uuid_redis = await func(jti)
    return uuid == uuid_redis


@pytest.mark.asyncio
@pytest.mark.parametrize('data,result,code', user_data)
async def test_register(data, result, code, make_post_request, clear_db_tables, clear_redis):

    response = await make_post_request(url=f'{url}/register', data=data)

    assert response.status == code
    assert response.body == result 


@pytest.mark.asyncio
@pytest.mark.parametrize('data,code', user_login)
async def test_login(data, code, make_post_request, clear_db_tables,  get_from_redis, clear_redis):

    await make_post_request(url=f'{url}/register', data=user_data[0][0])

    response = await make_post_request(url=f'{url}/login', data=data)

    assert response.status == code

    if code == HTTPStatus.OK:
        assert await check_tokens(response, get_from_redis)


@pytest.mark.asyncio
async def test_refresh(make_get_request, clear_db_tables, clear_redis, get_from_redis, prepare_user):

    _, headers_refresh, uuid = await prepare_user(url)

    response = await make_get_request(url=f'{url}/refresh/{uuid}', headers=headers_refresh)

    assert response.status == HTTPStatus.OK
    assert await check_tokens(response, get_from_redis)


@pytest.mark.asyncio
async def test_logout(make_get_request, clear_db_tables, clear_redis, prepare_user):

    headers = []

    for _ in range(2):
        headers_access, headers_refresh, uuid = await prepare_user(url)
        headers.append(Header(headers_access, headers_refresh, uuid))

    uuid = headers[0].uuid
    response = await make_get_request(url=f'{url}/logout/{uuid}?all_devices=false', headers=headers[0].header_access)
    assert response.status == HTTPStatus.OK

    for header, status in zip(headers,[HTTPStatus.UNAUTHORIZED, HTTPStatus.OK]):
        response = await make_get_request(url=f'{url}/history/{uuid}', headers=header.header_access)
        assert response.status == status

        response = await make_get_request(url=f'{url}/refresh/{uuid}', headers=header.header_refresh)
        assert response.status == status


@pytest.mark.asyncio
async def test_logout_all(make_get_request, clear_db_tables, clear_redis, prepare_user):

    headers = []

    @dataclass
    class Header:
        header_access: dict
        header_refresh: dict
        uuid: str

    for _ in range(2):
        headers_access, headers_refresh, uuid = await prepare_user(url)
        headers.append(Header(headers_access, headers_refresh, uuid))

    uuid = headers[0].uuid
    response = await make_get_request(url=f'{url}/logout/{uuid}?all_devices=true', headers=headers[0].header_access)
    assert response.status == HTTPStatus.OK

    for header in headers:
        response = await make_get_request(url=f'{url}/history/{uuid}', headers=header.header_access)
        assert response.status == HTTPStatus.UNAUTHORIZED

        response = await make_get_request(url=f'{url}/refresh/{uuid}', headers=header.header_refresh)
        assert response.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_user_change(make_post_request, make_put_request, clear_db_tables, clear_redis, get_from_redis, prepare_user):

    headers_access, _, uuid = await prepare_user(url)

    response = await make_put_request(url=f'{url}/{uuid}', headers=headers_access, data=update_user_data)
    assert response.status == HTTPStatus.OK

    response = await make_post_request(url=f'{url}/login', data=update_user_data)

    assert response.status == HTTPStatus.OK

    assert await check_tokens(response, get_from_redis)


@pytest.mark.asyncio
async def test_user_history(make_get_request, clear_db_tables, clear_redis, prepare_user):

    headers_access = None
    uuid = None
    headers_access, _, uuid = await prepare_user(url)

    response = await make_get_request(url=f'{url}/history/{uuid}?page_num=1&page_items=5', headers=headers_access)

    assert response.status == HTTPStatus.OK
    assert len(response.body) == 1


