class CrawlerError(Exception):
    """Base error for crawling failures."""


class CrawlerFetchError(CrawlerError):
    """Raised when an HTTP response cannot be fetched successfully."""


class CrawlerParseError(CrawlerError):
    """Raised when required site markup is missing or malformed."""


class CrawlerPageLimitError(CrawlerError):
    """Raised when pagination cannot reach a safe stopping point."""

