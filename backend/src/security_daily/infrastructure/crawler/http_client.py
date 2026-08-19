import time
from collections.abc import Callable

import httpx

from security_daily.infrastructure.crawler.config import CrawlerConfig
from security_daily.infrastructure.crawler.errors import CrawlerFetchError


class BoanNewsHttpClient:
    def __init__(
        self,
        config: CrawlerConfig,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._config = config
        self._client = client or httpx.Client(
            timeout=config.timeout_seconds,
            headers={"User-Agent": config.user_agent},
            follow_redirects=True,
        )
        self._owns_client = client is None
        self._sleeper = sleeper

    def get_html(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries + 1):
            try:
                response = self._client.get(url)
                if response.status_code == 429 or response.status_code >= 500:
                    raise CrawlerFetchError(
                        f"Retryable response {response.status_code} for {url}"
                    )
                response.raise_for_status()
                response.encoding = "euc-kr"
                return response.text
            except (httpx.TimeoutException, httpx.TransportError, CrawlerFetchError) as error:
                last_error = error
                if attempt < self._config.max_retries:
                    self._sleeper(float(2**attempt))
                    continue
            except httpx.HTTPStatusError as error:
                raise CrawlerFetchError(
                    f"Non-success response {error.response.status_code} for {url}"
                ) from error
            break
        raise CrawlerFetchError(f"Failed to fetch {url}") from last_error

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "BoanNewsHttpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

