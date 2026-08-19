import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from time import perf_counter
from typing import Callable, Protocol

from security_daily.agents.selector.schemas import SelectorDecision
from security_daily.domain import Article, DailySelection
from security_daily.domain.repositories import (
    ArticleRepository,
    DailySelectionRepository,
)


logger = logging.getLogger(__name__)


class ArticleSelector(Protocol):
    model_name: str

    def select(self, articles: list[Article]) -> list[SelectorDecision]: ...


@dataclass(frozen=True, slots=True)
class SelectDailyNewsResult:
    target_date: date
    candidate_count: int
    selected_count: int
    model_name: str
    elapsed_seconds: float


class SelectDailyNews:
    def __init__(
        self,
        article_repository: ArticleRepository,
        selection_repository: DailySelectionRepository,
        selector: ArticleSelector,
        timer: Callable[[], float] = perf_counter,
    ) -> None:
        self._article_repository = article_repository
        self._selection_repository = selection_repository
        self._selector = selector
        self._timer = timer

    def execute(
        self, target_date: date, selected_at: datetime
    ) -> SelectDailyNewsResult:
        started = self._timer()
        articles = self._article_repository.list_published_on(target_date)
        logger.info(
            "selector_started target_date=%s candidate_count=%s model=%s",
            target_date,
            len(articles),
            self._selector.model_name,
        )
        try:
            decisions = self._selector.select(articles)
            selections = [
                DailySelection(
                    article_id=decision.article_id,
                    selection_date=target_date,
                    rank=decision.rank,
                    score=Decimal(str(decision.score)),
                    reason=decision.reason,
                    model_name=self._selector.model_name,
                    created_at=selected_at,
                )
                for decision in decisions
            ]
            self._selection_repository.replace_for_date(target_date, selections)
        except Exception as error:
            logger.error(
                "selector_failed target_date=%s candidate_count=%s model=%s "
                "error_type=%s elapsed_seconds=%.3f",
                target_date,
                len(articles),
                self._selector.model_name,
                type(error).__name__,
                self._timer() - started,
            )
            raise

        elapsed = self._timer() - started
        logger.info(
            "selector_succeeded target_date=%s candidate_count=%s "
            "selected_count=%s model=%s elapsed_seconds=%.3f",
            target_date,
            len(articles),
            len(selections),
            self._selector.model_name,
            elapsed,
        )
        return SelectDailyNewsResult(
            target_date,
            len(articles),
            len(selections),
            self._selector.model_name,
            elapsed,
        )
