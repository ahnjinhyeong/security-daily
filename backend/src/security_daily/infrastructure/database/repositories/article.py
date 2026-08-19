from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from security_daily.domain import Article
from security_daily.infrastructure.database.models import ArticleModel


class ArticleAlreadyExistsError(Exception):
    """Raised when an article violates one of its identity constraints."""


class SQLAlchemyArticleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def exists_by_source_id(self, source: str, source_article_id: str) -> bool:
        statement = select(ArticleModel.id).where(
            ArticleModel.source == source,
            ArticleModel.source_article_id == source_article_id,
        )
        return self._session.scalar(statement) is not None

    def add(self, article: Article) -> Article:
        model = ArticleModel(
            source=article.source,
            source_article_id=article.source_article_id,
            title=article.title,
            url=article.url,
            content=article.content,
            published_at=article.published_at,
            collected_at=article.collected_at,
        )
        self._session.add(model)
        try:
            self._session.commit()
            self._session.refresh(model)
        except IntegrityError as error:
            self._session.rollback()
            raise ArticleAlreadyExistsError(
                f"Article already exists: {article.source}/{article.source_article_id}"
            ) from error
        return self._to_domain(model)

    def list_published_on(self, target_date: date) -> list[Article]:
        start = datetime.combine(
            target_date, time.min, tzinfo=ZoneInfo("Asia/Seoul")
        )
        statement = (
            select(ArticleModel)
            .where(
                ArticleModel.published_at >= start,
                ArticleModel.published_at < start + timedelta(days=1),
            )
            .order_by(ArticleModel.published_at, ArticleModel.id)
        )
        return [self._to_domain(model) for model in self._session.scalars(statement)]

    def get_by_ids(self, article_ids: list[int]) -> list[Article]:
        if not article_ids:
            return []
        models = self._session.scalars(
            select(ArticleModel).where(ArticleModel.id.in_(article_ids))
        ).all()
        by_id = {model.id: model for model in models}
        return [self._to_domain(by_id[article_id]) for article_id in article_ids if article_id in by_id]

    @staticmethod
    def _to_domain(model: ArticleModel) -> Article:
        return Article(
            id=model.id,
            source=model.source,
            source_article_id=model.source_article_id,
            title=model.title,
            url=model.url,
            content=model.content,
            published_at=model.published_at,
            collected_at=model.collected_at,
            created_at=model.created_at,
        )
