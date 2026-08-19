from dataclasses import dataclass
from datetime import date, datetime

from security_daily.application.analyze_security_article import AnalyzeSecurityArticle
from security_daily.application.summarize_article import SummarizeArticle
from security_daily.domain import Article
from security_daily.domain.repositories import ArticleRepository, DailySelectionRepository


@dataclass(frozen=True, slots=True)
class ProcessArticlesResult:
    article_count: int
    processed_count: int
    skipped_count: int
    article_elapsed_seconds: dict[int, float]


class SelectedArticles:
    def __init__(self, articles: ArticleRepository, selections: DailySelectionRepository) -> None:
        self._articles = articles
        self._selections = selections

    def list_for_date(self, target_date: date) -> list[Article]:
        selected = self._selections.list_for_date(target_date)
        return self._articles.get_by_ids([item.article_id for item in selected])


class SummarizeSelectedArticles:
    def __init__(self, selected: SelectedArticles, summarize: SummarizeArticle) -> None:
        self._selected = selected
        self._summarize = summarize

    def execute(self, target_date: date, at: datetime) -> ProcessArticlesResult:
        articles = self._selected.list_for_date(target_date)
        results = [self._summarize.execute(article, at) for article in articles]
        return ProcessArticlesResult(
            len(articles),
            sum(not result.skipped for result in results),
            sum(result.skipped for result in results),
            {result.article_id: result.elapsed_seconds for result in results},
        )


class AnalyzeSelectedArticles:
    def __init__(self, selected: SelectedArticles, analyze: AnalyzeSecurityArticle) -> None:
        self._selected = selected
        self._analyze = analyze

    def execute(self, target_date: date, at: datetime) -> ProcessArticlesResult:
        articles = self._selected.list_for_date(target_date)
        results = [self._analyze.execute(article, at) for article in articles]
        return ProcessArticlesResult(
            len(articles),
            sum(not result.skipped for result in results),
            sum(result.skipped for result in results),
            {result.article_id: result.elapsed_seconds for result in results},
        )
