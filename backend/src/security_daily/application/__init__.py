"""Application use cases."""

from security_daily.application.collect_daily_news import (
    CollectDailyNews,
    CollectDailyNewsResult,
)
from security_daily.application.daily_pipeline import DailyPipeline, DailyPipelineResult
from security_daily.application.select_daily_news import (
    SelectDailyNews,
    SelectDailyNewsResult,
)
from security_daily.application.summarize_article import SummarizeArticle
from security_daily.application.analyze_security_article import AnalyzeSecurityArticle
from security_daily.application.process_selected_articles import (
    AnalyzeSelectedArticles,
    ProcessArticlesResult,
    SelectedArticles,
    SummarizeSelectedArticles,
)
from security_daily.application.generate_daily_quiz import GenerateDailyQuiz, GenerateDailyQuizResult
from security_daily.application.get_quizzes import GetQuizzes, PublicQuiz
from security_daily.application.grade_quiz_answer import (
    EmptyQuizAnswerError,
    GradeQuizAnswer,
    GradeQuizAnswerResult,
    QuizNotFoundError,
    is_quiz_answer_correct,
    normalize_quiz_answer,
)
from security_daily.application.get_news_briefing import GetNewsBriefing, NewsBriefing

__all__ = [
    "CollectDailyNews",
    "CollectDailyNewsResult",
    "DailyPipeline",
    "DailyPipelineResult",
    "SelectDailyNews",
    "SelectDailyNewsResult",
    "SummarizeArticle",
    "AnalyzeSecurityArticle",
    "AnalyzeSelectedArticles",
    "ProcessArticlesResult",
    "SelectedArticles",
    "SummarizeSelectedArticles",
    "GenerateDailyQuiz",
    "GenerateDailyQuizResult",
    "GetQuizzes",
    "PublicQuiz",
    "EmptyQuizAnswerError",
    "GradeQuizAnswer",
    "GradeQuizAnswerResult",
    "QuizNotFoundError",
    "is_quiz_answer_correct",
    "normalize_quiz_answer",
    "GetNewsBriefing",
    "NewsBriefing",
]
