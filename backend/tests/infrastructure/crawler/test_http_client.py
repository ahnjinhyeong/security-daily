import httpx
import pytest

from security_daily.infrastructure.crawler.config import CrawlerConfig
from security_daily.infrastructure.crawler.errors import CrawlerFetchError
from security_daily.infrastructure.crawler.http_client import BoanNewsHttpClient


def make_config(max_retries: int = 2) -> CrawlerConfig:
    return CrawlerConfig(
        base_url="https://www.boannews.com",
        timeout_seconds=1,
        max_retries=max_retries,
        max_pages=10,
        user_agent="SecurityDaily/Test",
    )


def test_http_client_decodes_euc_kr_response() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content="보안뉴스".encode("euc-kr"),
            headers={"Content-Type": "text/html; Charset=EUC-KR"},
            request=request,
        )
    )
    client = httpx.Client(transport=transport)

    html = BoanNewsHttpClient(make_config(), client=client).get_html(
        "https://www.boannews.com/test"
    )

    assert html == "보안뉴스"


def test_http_client_retries_server_error() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            503 if attempts == 1 else 200,
            text="ok",
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    crawler_client = BoanNewsHttpClient(
        make_config(), client=client, sleeper=delays.append
    )

    assert crawler_client.get_html("https://www.boannews.com/test") == "ok"
    assert attempts == 2
    assert delays == [1.0]


def test_http_client_does_not_retry_not_found() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(404, request=request))
    )

    with pytest.raises(CrawlerFetchError, match="404"):
        BoanNewsHttpClient(make_config(), client=client).get_html(
            "https://www.boannews.com/missing"
        )

