import os

import pytest

from security_daily.config import get_settings
from security_daily.jobs.daily import run_daily_job
from security_daily.infrastructure.crawler.config import CrawlerConfig
from security_daily.infrastructure.crawler.http_client import BoanNewsHttpClient
from security_daily.infrastructure.crawler.parsers import (
    BoanNewsDetailParser,
    BoanNewsListParser,
)


@pytest.mark.smoke
def test_live_boannews_list_and_detail_markup() -> None:
    if os.getenv("RUN_LIVE_SMOKE") != "1":
        pytest.skip("Set RUN_LIVE_SMOKE=1 to call the live website")

    config = CrawlerConfig.from_settings(get_settings())
    with BoanNewsHttpClient(config) as http_client:
        items = BoanNewsListParser(config.base_url).parse(
            http_client.get_html(f"{config.base_url}/media/t_list.asp?Page=1&kind=")
        )
        assert items

        first = items[0]
        detail = BoanNewsDetailParser().parse(
            http_client.get_html(first.url),
            source_article_id=first.source_article_id,
            url=first.url,
        )

    assert detail.source_article_id == first.source_article_id
    assert detail.title
    assert detail.content


@pytest.mark.smoke
def test_live_daily_job_pipeline() -> None:
    if os.getenv("RUN_LIVE_DAILY_JOB_SMOKE") != "1":
        pytest.skip(
            "Set RUN_LIVE_DAILY_JOB_SMOKE=1 to run the live job against PostgreSQL"
        )

    result = run_daily_job()

    assert result.run_id > 0
    assert result.collection.target_date
    assert (
        result.collection.saved_count + result.collection.duplicate_count
        == result.collection.crawled_count
    )
