from datetime import datetime
from typing import Any, Protocol

from security_daily.domain.ai_analysis import AiAnalysis


class AiAnalysisRepository(Protocol):
    def get_by_article_id(self, article_id: int) -> AiAnalysis | None: ...
    def mark_summary_running(self, article_id: int, at: datetime) -> None: ...
    def save_summary(
        self, article_id: int, summary: str, model_name: str, at: datetime
    ) -> None: ...
    def mark_summary_failed(
        self, article_id: int, error_type: str, at: datetime
    ) -> None: ...
    def mark_analyst_running(self, article_id: int, at: datetime) -> None: ...
    def save_analysis(
        self,
        article_id: int,
        importance: str,
        attack_scenario: str,
        security_actions: list[str],
        key_concepts: list[dict[str, str]],
        related_security_info: list[dict[str, str]],
        model_name: str,
        at: datetime,
    ) -> None: ...
    def mark_analyst_failed(
        self, article_id: int, error_type: str, at: datetime
    ) -> None: ...
