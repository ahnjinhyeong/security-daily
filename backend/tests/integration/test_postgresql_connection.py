import pytest
from pydantic import ValidationError
from sqlalchemy import text

from security_daily.config import get_settings
from security_daily.infrastructure.database import create_database_engine


@pytest.mark.integration
def test_postgresql_connection() -> None:
    try:
        database_url = get_settings().database_url
    except ValidationError:
        pytest.skip("DATABASE_URL is not configured")

    engine = create_database_engine(database_url)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
    finally:
        engine.dispose()

