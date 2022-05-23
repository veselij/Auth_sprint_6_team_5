import logging
from functools import wraps
from time import sleep

from utils.exceptions import RetryExceptionError


def expo(start_sleep_time, factor, border_sleep_time):
    """Generate exponential sequence.

    Args:
        start_sleep_time: float start repeat time
        factor: int exponential factor
        border_sleep_time: int exponential limit

    Description:
        t = start_sleep_time * factor^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time

    Yields:
        float: exponential sequence member
    """
    start = start_sleep_time
    sequence_element = 1
    while True:
        yield start
        start = start_sleep_time * factor**sequence_element
        if start > border_sleep_time:
            start = border_sleep_time
        sequence_element += 1


def backoff(logger: logging.Logger, start_sleep_time: float = 0.1, factor: int = 2, border_sleep_time: int = 10):
    """Repeat function with exponential delay in case it raises RetryException.

    Args:
        start_sleep_time: float start repeat time
        factor: int exponential factor
        border_sleep_time: int exponential limit
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            delays = expo(start_sleep_time, factor, border_sleep_time)
            func_result = None
            while True:
                try:
                    func_result = func(*args, **kwargs)
                except RetryExceptionError as e:
                    logger.exception(e)
                    delay = next(delays)
                else:
                    break
                sleep(delay)
            return func_result

        return inner

    return func_wrapper
