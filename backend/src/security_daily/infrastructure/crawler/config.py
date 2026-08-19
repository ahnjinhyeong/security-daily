from dataclasses import dataclass

from security_daily.config import Settings


@dataclass(frozen=True, slots=True)
class CrawlerConfig:
    base_url: str
    timeout_seconds: float
    max_retries: int
    max_pages: int
    user_agent: str

    @classmethod
    def from_settings(cls, settings: Settings) -> "CrawlerConfig":
        return cls(
            base_url=settings.boannews_base_url.rstrip("/"),
            timeout_seconds=settings.crawler_timeout_seconds,
            max_retries=settings.crawler_max_retries,
            max_pages=settings.crawler_max_pages,
            user_agent=settings.crawler_user_agent,
        )

