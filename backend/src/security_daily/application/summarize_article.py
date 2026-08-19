import logging
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Callable, Protocol

from security_daily.agents.summary.schemas import SummaryOutput
from security_daily.domain import AnalysisStatus, Article
from security_daily.domain.repositories import AiAnalysisRepository


logger = logging.getLogger(__name__)


class ArticleSummarizer(Protocol):
    model_name: str
    def summarize(self, article: Article) -> SummaryOutput: ...


@dataclass(frozen=True, slots=True)
class SummarizeArticleResult:
    article_id: int
    skipped: bool
    elapsed_seconds: float


class SummarizeArticle:
    def __init__(self, agent: ArticleSummarizer, repository: AiAnalysisRepository, timer: Callable[[], float] = perf_counter) -> None:
        self._agent = agent
        self._repository = repository
        self._timer = timer

    def execute(self, article: Article, at: datetime) -> SummarizeArticleResult:
        if article.id is None:
            raise ValueError("article must have an id")
        existing = self._repository.get_by_article_id(article.id)
        if existing and existing.summary_status is AnalysisStatus.SUCCESS:
            return SummarizeArticleResult(article.id, True, 0.0)
        started = self._timer()
        logger.info("summary_started article_id=%s model=%s", article.id, self._agent.model_name)
        self._repository.mark_summary_running(article.id, at)
        try:
            output = self._agent.summarize(article)
            self._repository.save_summary(article.id, output.summary, self._agent.model_name, at)
        except Exception as error:
            self._repository.mark_summary_failed(article.id, type(error).__name__, at)
            logger.error("summary_failed article_id=%s model=%s error_type=%s", article.id, self._agent.model_name, type(error).__name__)
            raise
        elapsed = self._timer() - started
        logger.info("summary_succeeded article_id=%s model=%s elapsed_seconds=%.3f", article.id, self._agent.model_name, elapsed)
        return SummarizeArticleResult(article.id, False, elapsed)
