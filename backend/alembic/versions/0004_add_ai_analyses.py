"""Add ai analyses and analysis pipeline stages.

Revision ID: 0004_add_ai_analyses
Revises: 0003_add_daily_selections
Create Date: 2026-08-20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_add_ai_analyses"
down_revision: str | Sequence[str] | None = "0003_add_daily_selections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("importance", sa.Text(), nullable=True),
        sa.Column("attack_scenario", sa.Text(), nullable=True),
        sa.Column("security_actions", postgresql.JSONB(), nullable=True),
        sa.Column("key_concepts", postgresql.JSONB(), nullable=True),
        sa.Column("related_security_info", postgresql.JSONB(), nullable=True),
        sa.Column("summary_model", sa.Text(), nullable=True),
        sa.Column("analyst_model", sa.Text(), nullable=True),
        sa.Column("summary_status", sa.Text(), nullable=False),
        sa.Column("analyst_status", sa.Text(), nullable=False),
        sa.Column("error_type", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("summary_status IN ('PENDING','RUNNING','SUCCESS','FAILED')", name="ck_ai_analyses_summary_status"),
        sa.CheckConstraint("analyst_status IN ('PENDING','RUNNING','SUCCESS','FAILED')", name="ck_ai_analyses_analyst_status"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id"),
    )
    op.drop_constraint("ck_pipeline_runs_stage", "pipeline_runs", type_="check")
    op.create_check_constraint(
        "ck_pipeline_runs_stage",
        "pipeline_runs",
        "stage IN ('COLLECT', 'SELECT', 'SUMMARY', 'ANALYZE')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_pipeline_runs_stage", "pipeline_runs", type_="check")
    op.create_check_constraint(
        "ck_pipeline_runs_stage", "pipeline_runs", "stage IN ('COLLECT', 'SELECT')"
    )
    op.drop_table("ai_analyses")
