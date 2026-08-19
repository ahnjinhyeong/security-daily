import logging
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Callable, Protocol

from security_daily.agents.analyst.schemas import AnalystOutput
from security_daily.domain import AnalysisStatus, Article
from security_daily.domain.repositories import AiAnalysisRepository


logger = logging.getLogger(__name__)


class ArticleAnalyst(Protocol):
    model_name: str
    def analyze(self, article: Article, summary: str) -> AnalystOutput: ...


@dataclass(frozen=True, slots=True)
class AnalyzeSecurityArticleResult:
    article_id: int
    skipped: bool
    elapsed_seconds: float


class AnalyzeSecurityArticle:
    def __init__(self, agent: ArticleAnalyst, repository: AiAnalysisRepository, timer: Callable[[], float] = perf_counter) -> None:
        self._agent = agent
        self._repository = repository
        self._timer = timer

    def execute(self, article: Article, at: datetime) -> AnalyzeSecurityArticleResult:
        if article.id is None:
            raise ValueError("article must have an id")
        existing = self._repository.get_by_article_id(article.id)
        if existing is None or existing.summary_status is not AnalysisStatus.SUCCESS or not existing.summary:
            raise ValueError("successful summary is required before analysis")
        if existing.analyst_status is AnalysisStatus.SUCCESS:
            return AnalyzeSecurityArticleResult(article.id, True, 0.0)
        started = self._timer()
        logger.info("analyst_started article_id=%s model=%s", article.id, self._agent.model_name)
        self._repository.mark_analyst_running(article.id, at)
        try:
            output = self._agent.analyze(article, existing.summary)
            self._repository.save_analysis(
                article.id,
                output.importance,
                output.attack_scenario,
                output.security_actions,
                [item.model_dump() for item in output.key_concepts],
                [item.model_dump() for item in output.related_security_info],
                self._agent.model_name,
                at,
            )
        except Exception as error:
            self._repository.mark_analyst_failed(article.id, type(error).__name__, at)
            logger.error("analyst_failed article_id=%s model=%s error_type=%s", article.id, self._agent.model_name, type(error).__name__)
            raise
        elapsed = self._timer() - started
        logger.info("analyst_succeeded article_id=%s model=%s elapsed_seconds=%.3f", article.id, self._agent.model_name, elapsed)
        return AnalyzeSecurityArticleResult(article.id, False, elapsed)
