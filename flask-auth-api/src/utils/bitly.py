import requests

from core.config import config, logger
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def get_short_link(url: str) -> str:

    headers = {
        "Authorization": f"Bearer {config.bitly_api_access_token}",
        "Content-Type": "application/json",
    }

    data = {"long_url": url, "domain": "bit.ly"}

    try:
        response = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers=headers,
            data=data,
        )
    except requests.exceptions.RequestException:
        raise RetryExceptionError("Bitly connection error")
    try:
        body = response.json()
        return body["link"]
    except (requests.JSONDecodeError, KeyError):
        logger.exception("not able to decode response from Bitly")
        return url
