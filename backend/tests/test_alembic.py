from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from security_daily.infrastructure.database import Base


def test_alembic_configuration_loads() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(backend_root / "alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert Path(scripts.dir).resolve() == (backend_root / "alembic").resolve()
    assert set(Base.metadata.tables) == {
        "ai_analyses",
        "articles",
        "daily_selections",
        "pipeline_runs",
        "quizzes",
        "quiz_attempts",
    }
