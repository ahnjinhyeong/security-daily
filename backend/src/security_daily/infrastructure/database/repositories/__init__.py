"""SQLAlchemy repository implementations."""

from security_daily.infrastructure.database.repositories.article import (
    ArticleAlreadyExistsError,
    SQLAlchemyArticleRepository,
)
from security_daily.infrastructure.database.repositories.ai_analysis import (
    SQLAlchemyAiAnalysisRepository,
)
from security_daily.infrastructure.database.repositories.daily_selection import (
    DailySelectionConstraintError,
    SQLAlchemyDailySelectionRepository,
)
from security_daily.infrastructure.database.repositories.pipeline_run import (
    SQLAlchemyPipelineRunRepository,
)
from security_daily.infrastructure.database.repositories.quiz import SQLAlchemyQuizRepository
from security_daily.infrastructure.database.repositories.quiz_attempt import SQLAlchemyQuizAttemptRepository
from security_daily.infrastructure.database.repositories.news_query import SQLAlchemyNewsQueryRepository

__all__ = [
    "ArticleAlreadyExistsError",
    "SQLAlchemyArticleRepository",
    "SQLAlchemyAiAnalysisRepository",
    "DailySelectionConstraintError",
    "SQLAlchemyDailySelectionRepository",
    "SQLAlchemyPipelineRunRepository",
    "SQLAlchemyQuizRepository",
    "SQLAlchemyQuizAttemptRepository",
    "SQLAlchemyNewsQueryRepository",
]
