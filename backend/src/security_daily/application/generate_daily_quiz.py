import logging
from dataclasses import dataclass
from datetime import date, datetime
from time import perf_counter
from typing import Callable, Protocol

from security_daily.agents.quiz.schemas import QuizItem
from security_daily.domain import AiAnalysis, AnalysisStatus, Article, Quiz
from security_daily.domain.repositories import (
    AiAnalysisRepository,
    ArticleRepository,
    DailySelectionRepository,
    QuizRepository,
)


logger = logging.getLogger(__name__)


class DailyQuizAgent(Protocol):
    model_name: str
    def generate(self, inputs: list[tuple[Article, AiAnalysis]]) -> list[QuizItem]: ...


@dataclass(frozen=True, slots=True)
class GenerateDailyQuizResult:
    candidate_count: int
    generated_count: int
    saved_count: int
    skipped: bool
    elapsed_seconds: float
    model_name: str


class GenerateDailyQuiz:
    def __init__(
        self,
        articles: ArticleRepository,
        selections: DailySelectionRepository,
        analyses: AiAnalysisRepository,
        quizzes: QuizRepository,
        agent: DailyQuizAgent,
        timer: Callable[[], float] = perf_counter,
    ) -> None:
        self._articles = articles
        self._selections = selections
        self._analyses = analyses
        self._quizzes = quizzes
        self._agent = agent
        self._timer = timer

    def execute(self, target_date: date, at: datetime) -> GenerateDailyQuizResult:
        existing = self._quizzes.list_for_date(target_date)
        if existing:
            return GenerateDailyQuizResult(len(existing), 0, 0, True, 0.0, self._agent.model_name)

        selected = self._selections.list_for_date(target_date)
        articles = self._articles.get_by_ids([item.article_id for item in selected])
        article_by_id = {article.id: article for article in articles}
        inputs: list[tuple[Article, AiAnalysis]] = []
        for selection in selected:
            article = article_by_id.get(selection.article_id)
            analysis = self._analyses.get_by_article_id(selection.article_id)
            if article is None or analysis is None or analysis.analyst_status is not AnalysisStatus.SUCCESS:
                raise ValueError("all selected articles require successful analysis")
            inputs.append((article, analysis))

        started = self._timer()
        logger.info("quiz_started target_date=%s candidate_count=%s model=%s", target_date, len(inputs), self._agent.model_name)
        try:
            generated = self._agent.generate(inputs)
            quizzes = [
                Quiz(
                    article_id=item.article_id,
                    quiz_date=target_date,
                    question=item.question,
                    answer=item.answer,
                    accepted_answers=item.accepted_answers,
                    explanation=item.explanation,
                    model_name=self._agent.model_name,
                    created_at=at,
                )
                for item in generated
            ]
            saved = self._quizzes.save_for_date(target_date, quizzes)
        except Exception as error:
            logger.error("quiz_failed target_date=%s model=%s error_type=%s", target_date, self._agent.model_name, type(error).__name__)
            raise
        elapsed = self._timer() - started
        logger.info("quiz_succeeded target_date=%s generated_count=%s saved_count=%s model=%s elapsed_seconds=%.3f", target_date, len(generated), len(saved), self._agent.model_name, elapsed)
        return GenerateDailyQuizResult(len(inputs), len(generated), len(saved), False, elapsed, self._agent.model_name)
