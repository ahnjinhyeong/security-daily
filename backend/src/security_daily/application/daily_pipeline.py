import logging
from dataclasses import dataclass
from datetime import date, datetime
from time import perf_counter
from typing import Callable

from security_daily.application.collect_daily_news import CollectDailyNews, CollectDailyNewsResult
from security_daily.application.select_daily_news import SelectDailyNews, SelectDailyNewsResult
from security_daily.application.process_selected_articles import (
    AnalyzeSelectedArticles,
    ProcessArticlesResult,
    SummarizeSelectedArticles,
)
from security_daily.application.generate_daily_quiz import GenerateDailyQuiz, GenerateDailyQuizResult
from security_daily.domain import PipelineStage
from security_daily.domain.repositories import PipelineRunRepository
from security_daily.infrastructure.crawler.boannews import KST, previous_date_kst


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DailyPipelineResult:
    run_id: int
    collection: CollectDailyNewsResult | None
    selection: SelectDailyNewsResult | None
    elapsed_seconds: float
    selection_run_id: int | None = None
    summary: ProcessArticlesResult | None = None
    analysis: ProcessArticlesResult | None = None
    summary_run_id: int | None = None
    analysis_run_id: int | None = None
    quiz: GenerateDailyQuizResult | None = None
    quiz_run_id: int | None = None


class DailyPipeline:
    def __init__(
        self,
        collector: CollectDailyNews,
        run_repository: PipelineRunRepository,
        selector: SelectDailyNews | None = None,
        clock: Callable[[], datetime] | None = None,
        timer: Callable[[], float] = perf_counter,
        summarizer: SummarizeSelectedArticles | None = None,
        analyzer: AnalyzeSelectedArticles | None = None,
        quiz_generator: GenerateDailyQuiz | None = None,
    ) -> None:
        self._collector = collector
        self._selector = selector
        self._run_repository = run_repository
        self._summarizer = summarizer
        self._analyzer = analyzer
        self._quiz_generator = quiz_generator
        self._clock = clock or (lambda: datetime.now(KST))
        self._timer = timer

    def execute(
        self,
        run_at: datetime | None = None,
        start_stage: PipelineStage = PipelineStage.COLLECT,
    ) -> DailyPipelineResult:
        effective_run_at = run_at or self._clock()
        if effective_run_at.tzinfo is None:
            raise ValueError("run_at must be timezone-aware")
        required = {
            PipelineStage.SELECT: self._selector,
            PipelineStage.SUMMARY: self._summarizer,
            PipelineStage.ANALYZE: self._analyzer,
            PipelineStage.QUIZ: self._quiz_generator,
        }
        if start_stage in required and required[start_stage] is None:
            raise ValueError(f"{start_stage.value} stage is not configured")

        target_date = previous_date_kst(effective_run_at)
        pipeline_started = self._timer()
        collection: CollectDailyNewsResult | None = None
        selection: SelectDailyNewsResult | None = None
        collect_run_id: int | None = None
        select_run_id: int | None = None
        summary: ProcessArticlesResult | None = None
        analysis: ProcessArticlesResult | None = None
        summary_run_id: int | None = None
        analysis_run_id: int | None = None
        quiz: GenerateDailyQuizResult | None = None
        quiz_run_id: int | None = None
        logger.info(
            "daily_pipeline_started target_date=%s start_stage=%s",
            target_date,
            start_stage.value,
        )

        try:
            if start_stage is PipelineStage.COLLECT:
                collect_run_id, collection = self._execute_collect(
                    effective_run_at, target_date
                )

            if self._selector is not None and start_stage in (
                PipelineStage.COLLECT,
                PipelineStage.SELECT,
            ):
                select_run_id, selection = self._execute_select(
                    effective_run_at, target_date
                )
            if self._summarizer is not None and start_stage in (
                PipelineStage.COLLECT,
                PipelineStage.SELECT,
                PipelineStage.SUMMARY,
            ):
                summary_run_id, summary = self._execute_processing(
                    PipelineStage.SUMMARY, self._summarizer, effective_run_at, target_date
                )
            if self._analyzer is not None and start_stage is not PipelineStage.QUIZ:
                analysis_run_id, analysis = self._execute_processing(
                    PipelineStage.ANALYZE, self._analyzer, effective_run_at, target_date
                )
            if self._quiz_generator is not None:
                quiz_run_id, quiz = self._execute_quiz(effective_run_at, target_date)
        except Exception as error:
            logger.error(
                "daily_pipeline_failed target_date=%s error_type=%s "
                "elapsed_seconds=%.3f",
                target_date,
                type(error).__name__,
                self._timer() - pipeline_started,
            )
            raise

        elapsed = self._timer() - pipeline_started
        logger.info(
            "daily_pipeline_succeeded target_date=%s elapsed_seconds=%.3f",
            target_date,
            elapsed,
        )
        primary_run_id = next(
            (
                run_id
                for run_id in (collect_run_id, select_run_id, summary_run_id, analysis_run_id, quiz_run_id)
                if run_id is not None
            ),
            None,
        )
        if primary_run_id is None:
            raise RuntimeError("Daily pipeline did not execute a stage")
        return DailyPipelineResult(
            primary_run_id,
            collection,
            selection,
            elapsed,
            select_run_id,
            summary,
            analysis,
            summary_run_id,
            analysis_run_id,
            quiz,
            quiz_run_id,
        )

    def _execute_quiz(
        self, run_at: datetime, target_date: date
    ) -> tuple[int, GenerateDailyQuizResult]:
        if self._quiz_generator is None:
            raise RuntimeError("quiz generator is not configured")
        run_id = self._start_stage(target_date, PipelineStage.QUIZ, run_at)
        started = self._timer()
        try:
            result = self._quiz_generator.execute(target_date, run_at)
        except Exception as error:
            self._fail_stage(run_id, target_date, PipelineStage.QUIZ, error, started)
            raise
        self._run_repository.mark_success(run_id, self._clock(), 0, 0, 0)
        logger.info(
            "pipeline_stage_succeeded run_id=%s target_date=%s stage=QUIZ "
            "generated_count=%s saved_count=%s skipped=%s elapsed_seconds=%.3f",
            run_id,
            target_date,
            result.generated_count,
            result.saved_count,
            result.skipped,
            self._timer() - started,
        )
        return run_id, result

    def _execute_processing(
        self,
        stage: PipelineStage,
        use_case: SummarizeSelectedArticles | AnalyzeSelectedArticles,
        run_at: datetime,
        target_date: date,
    ) -> tuple[int, ProcessArticlesResult]:
        run_id = self._start_stage(target_date, stage, run_at)
        started = self._timer()
        try:
            result = use_case.execute(target_date, run_at)
        except Exception as error:
            self._fail_stage(run_id, target_date, stage, error, started)
            raise
        self._run_repository.mark_success(run_id, self._clock(), 0, 0, 0)
        logger.info(
            "pipeline_stage_succeeded run_id=%s target_date=%s stage=%s "
            "article_count=%s processed_count=%s skipped_count=%s elapsed_seconds=%.3f",
            run_id,
            target_date,
            stage.value,
            result.article_count,
            result.processed_count,
            result.skipped_count,
            self._timer() - started,
        )
        return run_id, result

    def _execute_collect(
        self, run_at: datetime, target_date: date
    ) -> tuple[int, CollectDailyNewsResult]:
        run_id = self._start_stage(target_date, PipelineStage.COLLECT, run_at)
        started = self._timer()
        try:
            result = self._collector.execute(run_at)
        except Exception as error:
            self._fail_stage(run_id, target_date, PipelineStage.COLLECT, error, started)
            raise
        self._run_repository.mark_success(
            run_id,
            self._clock(),
            result.crawled_count,
            result.saved_count,
            result.duplicate_count,
        )
        logger.info(
            "pipeline_stage_succeeded run_id=%s target_date=%s stage=COLLECT "
            "crawled_count=%s saved_count=%s duplicate_count=%s elapsed_seconds=%.3f",
            run_id,
            target_date,
            result.crawled_count,
            result.saved_count,
            result.duplicate_count,
            self._timer() - started,
        )
        return run_id, result

    def _execute_select(
        self, run_at: datetime, target_date: date
    ) -> tuple[int, SelectDailyNewsResult]:
        if self._selector is None:
            raise RuntimeError("selector is not configured")
        run_id = self._start_stage(target_date, PipelineStage.SELECT, run_at)
        started = self._timer()
        try:
            result = self._selector.execute(target_date, run_at)
        except Exception as error:
            self._fail_stage(run_id, target_date, PipelineStage.SELECT, error, started)
            raise
        self._run_repository.mark_success(
            run_id,
            self._clock(),
            0,
            0,
            0,
            candidate_count=result.candidate_count,
            selected_count=result.selected_count,
        )
        logger.info(
            "pipeline_stage_succeeded run_id=%s target_date=%s stage=SELECT "
            "candidate_count=%s selected_count=%s model=%s elapsed_seconds=%.3f",
            run_id,
            target_date,
            result.candidate_count,
            result.selected_count,
            result.model_name,
            self._timer() - started,
        )
        return run_id, result

    def _start_stage(
        self, target_date: date, stage: PipelineStage, created_at: datetime
    ) -> int:
        pipeline_run = self._run_repository.create_pending(
            target_date, stage, created_at
        )
        if pipeline_run.id is None:
            raise RuntimeError("Pipeline run repository did not assign an id")
        self._run_repository.mark_running(pipeline_run.id, self._clock())
        logger.info(
            "pipeline_stage_started run_id=%s target_date=%s stage=%s",
            pipeline_run.id,
            target_date,
            stage.value,
        )
        return pipeline_run.id

    def _fail_stage(
        self,
        run_id: int,
        target_date: date,
        stage: PipelineStage,
        error: Exception,
        started: float,
    ) -> None:
        error_type = type(error).__name__
        self._run_repository.mark_failed(run_id, self._clock(), error_type)
        logger.error(
            "pipeline_stage_failed run_id=%s target_date=%s stage=%s "
            "error_type=%s elapsed_seconds=%.3f",
            run_id,
            target_date,
            stage.value,
            error_type,
            self._timer() - started,
        )
