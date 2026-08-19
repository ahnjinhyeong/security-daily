"""Repository contracts used by application use cases."""

from security_daily.domain.repositories.article_repository import ArticleRepository
from security_daily.domain.repositories.ai_analysis_repository import AiAnalysisRepository
from security_daily.domain.repositories.daily_selection_repository import (
    DailySelectionRepository,
)
from security_daily.domain.repositories.pipeline_run_repository import PipelineRunRepository
from security_daily.domain.repositories.quiz_repository import QuizRepository
from security_daily.domain.repositories.quiz_attempt_repository import QuizAttemptRepository
from security_daily.domain.repositories.news_query_repository import NewsQueryRepository

__all__ = [
    "AiAnalysisRepository",
    "ArticleRepository",
    "DailySelectionRepository",
    "PipelineRunRepository",
    "QuizRepository",
    "QuizAttemptRepository",
    "NewsQueryRepository",
]
