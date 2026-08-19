"""Add quizzes and QUIZ pipeline stage.

Revision ID: 0005_add_quizzes
Revises: 0004_add_ai_analyses
Create Date: 2026-08-20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_add_quizzes"
down_revision: str | Sequence[str] | None = "0004_add_ai_analyses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quizzes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("quiz_date", sa.Date(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("accepted_answers", postgresql.JSONB(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_date", "question", name="uq_quizzes_date_question"),
    )
    op.create_index("ix_quizzes_quiz_date", "quizzes", ["quiz_date"])
    op.drop_constraint("ck_pipeline_runs_stage", "pipeline_runs", type_="check")
    op.create_check_constraint(
        "ck_pipeline_runs_stage",
        "pipeline_runs",
        "stage IN ('COLLECT', 'SELECT', 'SUMMARY', 'ANALYZE', 'QUIZ')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_pipeline_runs_stage", "pipeline_runs", type_="check")
    op.create_check_constraint(
        "ck_pipeline_runs_stage",
        "pipeline_runs",
        "stage IN ('COLLECT', 'SELECT', 'SUMMARY', 'ANALYZE')",
    )
    op.drop_index("ix_quizzes_quiz_date", table_name="quizzes")
    op.drop_table("quizzes")
