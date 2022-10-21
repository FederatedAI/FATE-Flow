import random
import time

from ..conf import REQUEST_MAX_WAIT_SEC, REQUEST_WAIT_SEC


def get_exponential_backoff_interval(retries, full_jitter=False):
    """Calculate the exponential backoff wait time."""
    # Will be zero if factor equals 0

    countdown = min(REQUEST_MAX_WAIT_SEC, REQUEST_WAIT_SEC * (2 ** retries))
    # Full jitter according to
    # https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    if full_jitter:
        countdown = random.randrange(countdown + 1)
    # Adjust according to maximum wait time and account for negative values.
    return max(0, countdown)

def current_timestamp():
    return int(time.time() * 1000)