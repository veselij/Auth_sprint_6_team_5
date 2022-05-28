import asyncio
from dataclasses import dataclass
from typing import Optional

import aiohttp
import jwt
import pytest
import pytest_asyncio
from multidict import CIMultiDictProxy


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest_asyncio.fixture(scope="session")
async def web_client():
    web_client = aiohttp.ClientSession()
    yield web_client
    await web_client.close()


@pytest.fixture
def make_get_request(web_client):
    async def inner(url: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> HTTPResponse:
        params = params or {}
        async with web_client.get(url, params=params, headers=headers) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def make_get_request_no_body(web_client):
    async def inner(url: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> HTTPResponse:
        params = params or {}
        async with web_client.get(url, params=params, headers=headers) as response:
            return HTTPResponse(
                body={},
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def make_post_request(web_client):
    async def inner(
        url: str, params: Optional[dict] = None, headers: Optional[dict] = None, data: Optional[dict] = None
    ) -> HTTPResponse:
        params = params or {}
        async with web_client.post(url, params=params, headers=headers, json=data) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def make_put_request(web_client):
    async def inner(
        url: str, params: Optional[dict] = None, headers: Optional[dict] = None, data: Optional[dict] = None
    ) -> HTTPResponse:
        params = params or {}
        async with web_client.put(url, params=params, headers=headers, json=data) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def make_delete_request(web_client):
    async def inner(
        url: str, params: Optional[dict] = None, headers: Optional[dict] = None, data: Optional[dict] = None
    ) -> HTTPResponse:
        params = params or {}
        async with web_client.delete(url, params=params, headers=headers, json=data) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def prepare_user(make_post_request):
    async def inner(url: str, user_data: dict):
        await make_post_request(url=f"{url}/register", data=user_data)

        response = await make_post_request(url=f"{url}/login", data=user_data)
        request_id = response.body["request_id"]
        
        totp_url = url.replace("users", "totp")
        response = await make_post_request(url=f"{totp_url}/check/{request_id}", data={"code": "1234"})
        refresh_token = response.body["refresh_token"]
        headers_refresh = {"Authorization": f"Bearer {refresh_token}"}

        access_token = response.body["access_token"]
        headers_access = {"Authorization": f"Bearer {access_token}"}

        uuid = jwt.decode(refresh_token, options={"verify_signature": False})["sub"]

        return headers_access, headers_refresh, uuid

    return inner
