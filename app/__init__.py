from ratelimit import limits, sleep_and_retry
from functools import wraps
import time

def rate_limited(max_calls: int, period: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            @sleep_and_retry
            @limits(calls=max_calls, period=period)
            def rate_limited_func():
                return func(*args, **kwargs)
            return rate_limited_func()
        return wrapper
    return decorator