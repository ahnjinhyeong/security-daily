from sqlalchemy import Engine
from security_daily.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


def test_engine_and_session_factory_use_postgresql_without_connecting() -> None:
    engine = create_database_engine(
        "postgresql+psycopg://user:password@localhost:5432/security_daily"
    )
    session_factory = create_session_factory(engine)

    try:
        assert isinstance(engine, Engine)
        assert engine.dialect.name == "postgresql"
        assert session_factory.kw["bind"] is engine
        assert session_factory.kw["autoflush"] is False
        assert session_factory.kw["expire_on_commit"] is False
        with session_factory() as session:
            assert session.get_bind() is engine
    finally:
        engine.dispose()
