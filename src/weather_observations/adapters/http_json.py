from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from weather_observations.domain.result import Err, Error, Ok, Result

USER_AGENT = "(weather-observations, https://github.com/trevorjdep/weather-observations)"


class JsonClient(Protocol):
    def get(self, url: str) -> Result[Any]: ...


class UrllibJsonClient:
    """Adapter: GETs a URL and parses the JSON body; transport trouble becomes an Error."""

    def __init__(self, timeout_seconds: float = 30) -> None:
        self._timeout = timeout_seconds

    def get(self, url: str) -> Result[Any]:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return Ok(json.load(response))
        except (urllib.error.URLError, TimeoutError) as error:
            return Err(Error("http.unavailable", f"{url}: {error}"))
        except json.JSONDecodeError as error:
            return Err(Error("http.unexpected_response", f"{url}: not JSON ({error})"))


class RetryingJsonClient:
    """Decorator: retries an unavailable source with growing pauses."""

    def __init__(
        self,
        inner: JsonClient,
        attempts: int = 3,
        pause_seconds: float = 2,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._inner = inner
        self._attempts = attempts
        self._pause = pause_seconds
        self._sleep = sleep

    def get(self, url: str) -> Result[Any]:
        result = self._inner.get(url)
        for attempt in range(1, self._attempts):
            if not (isinstance(result, Err) and result.error.code == "http.unavailable"):
                break
            self._sleep(self._pause * 2**attempt)
            result = self._inner.get(url)
        return result
