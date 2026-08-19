from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from security_daily.domain import BriefingArticle, NewsDateCount
from security_daily.infrastructure.database.models import (
    AiAnalysisModel,
    ArticleModel,
    DailySelectionModel,
)


class SQLAlchemyNewsQueryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_date(self, selection_date: date) -> list[BriefingArticle]:
        statement = (
            select(DailySelectionModel, ArticleModel, AiAnalysisModel)
            .join(ArticleModel, ArticleModel.id == DailySelectionModel.article_id)
            .outerjoin(AiAnalysisModel, AiAnalysisModel.article_id == ArticleModel.id)
            .where(DailySelectionModel.selection_date == selection_date)
            .order_by(DailySelectionModel.rank)
        )
        return [
            BriefingArticle(
                rank=selection.rank,
                article_id=article.id,
                title=article.title,
                url=article.url,
                published_at=article.published_at,
                summary=analysis.summary if analysis else None,
                importance=analysis.importance if analysis else None,
                attack_scenario=analysis.attack_scenario if analysis else None,
                security_actions=analysis.security_actions if analysis else None,
                key_concepts=analysis.key_concepts if analysis else None,
                related_security_info=(
                    analysis.related_security_info if analysis else None
                ),
            )
            for selection, article, analysis in self._session.execute(statement)
        ]

    def list_available_dates(self) -> list[NewsDateCount]:
        article_count = func.count(DailySelectionModel.article_id)
        statement = (
            select(DailySelectionModel.selection_date, article_count)
            .group_by(DailySelectionModel.selection_date)
            .order_by(DailySelectionModel.selection_date.desc())
        )
        return [
            NewsDateCount(date=selection_date, article_count=count)
            for selection_date, count in self._session.execute(statement)
        ]
