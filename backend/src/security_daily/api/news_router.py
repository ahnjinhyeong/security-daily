from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from security_daily.api.dependencies import get_news_query
from security_daily.api.schemas import (
    NewsArticleResponse,
    NewsBriefingResponse,
    NewsDateResponse,
    NewsInsightResponse,
)
from security_daily.application import GetNewsBriefing, NewsBriefing


router = APIRouter(prefix="/api/news", tags=["news"])


def _to_response(briefing: NewsBriefing) -> NewsBriefingResponse:
    return NewsBriefingResponse(
        date=briefing.date,
        count=briefing.count,
        articles=[
            NewsArticleResponse(
                id=article.article_id,
                rank=article.rank,
                title=article.title,
                url=article.url,
                published_at=article.published_at,
                summary=article.summary,
                insight=NewsInsightResponse(
                    importance=article.importance,
                    attack_scenario=article.attack_scenario,
                    security_actions=article.security_actions,
                    key_concepts=article.key_concepts,
                    related_security_info=article.related_security_info,
                ),
            )
            for article in briefing.articles
        ],
    )


@router.get("/today", response_model=NewsBriefingResponse)
def get_today_news(
    query_service: Annotated[GetNewsBriefing, Depends(get_news_query)],
) -> NewsBriefingResponse:
    return _to_response(query_service.for_today())


@router.get("/dates", response_model=list[NewsDateResponse])
def get_news_dates(
    query_service: Annotated[GetNewsBriefing, Depends(get_news_query)],
) -> list[NewsDateResponse]:
    return [
        NewsDateResponse.model_validate(item, from_attributes=True)
        for item in query_service.available_dates()
    ]


@router.get("", response_model=NewsBriefingResponse)
def get_news_by_date(
    query_service: Annotated[GetNewsBriefing, Depends(get_news_query)],
    target_date: Annotated[date, Query(alias="date")],
) -> NewsBriefingResponse:
    return _to_response(query_service.for_date(target_date))
