from datetime import UTC, datetime

import pytest

from security_daily.domain import Article


def make_article(**overrides: object) -> Article:
    values: dict[str, object] = {
        "source": "boannews",
        "source_article_id": "145190",
        "title": "보안 기사",
        "url": "https://www.boannews.com/media/view.asp?idx=145190",
        "content": "정제된 기사 본문",
        "published_at": datetime(2026, 8, 18, 15, 45, tzinfo=UTC),
        "collected_at": datetime(2026, 8, 19, 8, 30, tzinfo=UTC),
    }
    values.update(overrides)
    return Article(**values)  # type: ignore[arg-type]


def test_article_accepts_valid_values() -> None:
    article = make_article()

    assert article.source == "boannews"
    assert article.source_article_id == "145190"


@pytest.mark.parametrize("field_name", ["source", "source_article_id", "title", "url", "content"])
def test_article_rejects_blank_required_text(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_article(**{field_name: "  "})


def test_article_rejects_naive_datetimes() -> None:
    with pytest.raises(ValueError, match="published_at"):
        make_article(published_at=datetime(2026, 8, 18, 15, 45))

