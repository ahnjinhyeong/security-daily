from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from security_daily.api.dependencies import get_quiz_grader, get_quiz_query
from security_daily.api.schemas import QuizAnswerRequest, QuizAnswerResponse, QuizResponse
from security_daily.application import GetQuizzes, GradeQuizAnswer, QuizNotFoundError


router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


@router.get("/today", response_model=list[QuizResponse])
def get_today_quizzes(
    query_service: Annotated[GetQuizzes, Depends(get_quiz_query)],
) -> list[QuizResponse]:
    return [QuizResponse.model_validate(quiz, from_attributes=True) for quiz in query_service.for_today_briefing()]


@router.get("", response_model=list[QuizResponse])
def get_quizzes_by_date(
    query_service: Annotated[GetQuizzes, Depends(get_quiz_query)],
    quiz_date: Annotated[date, Query(alias="date")],
) -> list[QuizResponse]:
    return [QuizResponse.model_validate(quiz, from_attributes=True) for quiz in query_service.for_date(quiz_date)]


@router.post("/{quiz_id}/answer", response_model=QuizAnswerResponse)
def answer_quiz(
    payload: QuizAnswerRequest,
    grader: Annotated[GradeQuizAnswer, Depends(get_quiz_grader)],
    quiz_id: Annotated[int, Path(gt=0)],
) -> QuizAnswerResponse:
    try:
        result = grader.execute(quiz_id, payload.answer)
    except QuizNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found") from exc
    return QuizAnswerResponse(
        correct=result.correct,
        correct_answer=result.correct_answer,
        explanation=result.explanation,
    )
