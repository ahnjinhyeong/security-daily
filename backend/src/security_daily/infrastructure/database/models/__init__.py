"""SQLAlchemy persistence models."""

from security_daily.infrastructure.database.models.article import ArticleModel
from security_daily.infrastructure.database.models.ai_analysis import AiAnalysisModel
from security_daily.infrastructure.database.models.daily_selection import (
    DailySelectionModel,
)
from security_daily.infrastructure.database.models.pipeline_run import PipelineRunModel
from security_daily.infrastructure.database.models.quiz import QuizModel
from security_daily.infrastructure.database.models.quiz_attempt import QuizAttemptModel

__all__ = ["AiAnalysisModel", "ArticleModel", "DailySelectionModel", "PipelineRunModel", "QuizModel", "QuizAttemptModel"]
