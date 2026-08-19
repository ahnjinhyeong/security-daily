from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from security_daily.config import get_settings


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy 2.x engine for the configured PostgreSQL database."""
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create sessions that keep transaction boundaries explicit."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@lru_cache
def get_engine() -> Engine:
    """Create the application engine only when database access is requested."""
    return create_database_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return create_session_factory(get_engine())


def get_db_session() -> Generator[Session, None, None]:
    """Yield one session and always release its connection afterwards."""
    with get_session_factory()() as session:
        yield session

