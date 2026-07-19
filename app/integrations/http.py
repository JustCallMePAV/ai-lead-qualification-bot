import time
from collections.abc import Callable

import httpx

TRANSIENT_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def post_with_retry(
    url: str,
    *,
    json: dict,
    timeout: float,
    headers: dict[str, str] | None = None,
    max_retries: int = 2,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """POST with bounded exponential backoff for transient transport/server failures."""
    for attempt in range(max_retries + 1):
        try:
            response = httpx.post(url, json=json, headers=headers, timeout=timeout)
            if response.status_code not in TRANSIENT_STATUS_CODES:
                response.raise_for_status()
                return response
            response.raise_for_status()
        except (httpx.TransportError, httpx.HTTPStatusError):
            if attempt >= max_retries:
                raise
            sleep(0.25 * (2**attempt))
    raise RuntimeError("Unreachable retry state")
