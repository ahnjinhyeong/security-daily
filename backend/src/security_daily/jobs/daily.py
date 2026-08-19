import argparse
import logging
from datetime import date, datetime, time, timedelta
from typing import Sequence

from security_daily.agents.selector import NewsSelectorAgent, SelectorInputBuilder
from security_daily.agents.summary import SummaryAgent
from security_daily.agents.analyst import SecurityAnalystAgent
from security_daily.agents.quiz import QuizAgent
from security_daily.application import (
    CollectDailyNews,
    DailyPipeline,
    DailyPipelineResult,
    SelectDailyNews,
    SummarizeArticle,
    AnalyzeSecurityArticle,
    SummarizeSelectedArticles,
    AnalyzeSelectedArticles,
    SelectedArticles,
    GenerateDailyQuiz,
)
from security_daily.config import get_settings
from security_daily.domain import PipelineStage
from security_daily.infrastructure.crawler.boannews import BoanNewsCrawler, KST
from security_daily.infrastructure.crawler.config import CrawlerConfig
from security_daily.infrastructure.crawler.http_client import BoanNewsHttpClient
from security_daily.infrastructure.database import get_session_factory
from security_daily.infrastructure.database.repositories import (
    SQLAlchemyArticleRepository,
    SQLAlchemyDailySelectionRepository,
    SQLAlchemyAiAnalysisRepository,
    SQLAlchemyPipelineRunRepository,
    SQLAlchemyQuizRepository,
)
from security_daily.infrastructure.llm import OllamaLLMProvider


logger = logging.getLogger(__name__)


def run_daily_job(
    run_at: datetime | None = None,
    start_stage: PipelineStage = PipelineStage.COLLECT,
) -> DailyPipelineResult:
    settings = get_settings()
    crawler_config = CrawlerConfig.from_settings(settings)

    with (
        get_session_factory()() as session,
        BoanNewsHttpClient(crawler_config) as http_client,
        OllamaLLMProvider(
            settings.ollama_base_url, settings.ollama_timeout_seconds
        ) as llm_provider,
    ):
        crawler = BoanNewsCrawler(crawler_config, http_client)
        article_repository = SQLAlchemyArticleRepository(session)
        collector = CollectDailyNews(
            crawler,
            article_repository,
        )
        selector_agent = NewsSelectorAgent(
            llm_provider,
            settings.selector_model,
            SelectorInputBuilder(
                settings.selector_max_content_chars,
                settings.selector_max_total_content_chars,
            ),
        )
        selector = SelectDailyNews(
            article_repository,
            SQLAlchemyDailySelectionRepository(session),
            selector_agent,
        )
        selection_repository = SQLAlchemyDailySelectionRepository(session)
        analysis_repository = SQLAlchemyAiAnalysisRepository(session)
        selected_articles = SelectedArticles(article_repository, selection_repository)
        summarizer = SummarizeSelectedArticles(
            selected_articles,
            SummarizeArticle(
                SummaryAgent(
                    llm_provider,
                    settings.summary_model,
                    settings.analysis_max_content_chars,
                ),
                analysis_repository,
            ),
        )
        analyzer = AnalyzeSelectedArticles(
            selected_articles,
            AnalyzeSecurityArticle(
                SecurityAnalystAgent(
                    llm_provider,
                    settings.analyst_model,
                    settings.analysis_max_content_chars,
                ),
                analysis_repository,
            ),
        )
        quiz_generator = GenerateDailyQuiz(
            article_repository,
            selection_repository,
            analysis_repository,
            SQLAlchemyQuizRepository(session),
            QuizAgent(llm_provider, settings.quiz_model),
        )
        pipeline = DailyPipeline(
            collector,
            SQLAlchemyPipelineRunRepository(session),
            selector,
            summarizer=summarizer,
            analyzer=analyzer,
            quiz_generator=quiz_generator,
        )
        return pipeline.execute(run_at, start_stage)


def _run_at_for_target_date(target_date: date) -> datetime:
    # 수집 Use Case가 실행일의 전날을 계산하므로 대상 날짜 다음 날 08:30으로 변환한다.
    return datetime.combine(
        target_date + timedelta(days=1), time(8, 30), tzinfo=KST
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Security Daily pipeline")
    parser.add_argument(
        "--target-date",
        type=date.fromisoformat,
        help="수집 대상 KST 날짜 (YYYY-MM-DD). 생략하면 현재 시각 기준 전날.",
    )
    parser.add_argument(
        "--start-stage",
        type=PipelineStage,
        choices=list(PipelineStage),
        default=PipelineStage.COLLECT,
        help="재실행 시작 단계. SELECT는 크롤링을 건너뛴다.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        run_daily_job(
            _run_at_for_target_date(args.target_date) if args.target_date else None,
            args.start_stage,
        )
    except Exception:
        # 상세 실패 로그와 상태 기록은 DailyPipeline이 담당한다.
        logger.error("daily_job_exited_with_failure")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
