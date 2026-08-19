"""Add daily selections and SELECT pipeline stage.

Revision ID: 0003_add_daily_selections
Revises: 0002_create_pipeline_runs
Create Date: 2026-08-19
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_daily_selections"
down_revision: str | Sequence[str] | None = "0002_create_pipeline_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_selections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("selection_date", sa.Date(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rank BETWEEN 1 AND 3", name="ck_daily_selections_rank"
        ),
        sa.CheckConstraint(
            "score BETWEEN 0 AND 100", name="ck_daily_selections_score"
        ),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "selection_date", "article_id", name="uq_daily_selections_date_article"
        ),
        sa.UniqueConstraint(
            "selection_date", "rank", name="uq_daily_selections_date_rank"
        ),
    )
    op.create_index(
        "ix_daily_selections_selection_date",
        "daily_selections",
        ["selection_date"],
    )

    op.drop_constraint("ck_pipeline_runs_stage", "pipeline_runs", type_="check")
    op.create_check_constraint(
        "ck_pipeline_runs_stage",
        "pipeline_runs",
        "stage IN ('COLLECT', 'SELECT')",
    )
    op.add_column(
        "pipeline_runs",
        sa.Column("candidate_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "pipeline_runs",
        sa.Column("selected_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_pipeline_runs_selection_counts_nonnegative",
        "pipeline_runs",
        "candidate_count >= 0 AND selected_count >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_pipeline_runs_selection_counts_nonnegative",
        "pipeline_runs",
        type_="check",
    )
    op.drop_column("pipeline_runs", "selected_count")
    op.drop_column("pipeline_runs", "candidate_count")
    op.drop_constraint("ck_pipeline_runs_stage", "pipeline_runs", type_="check")
    op.create_check_constraint(
        "ck_pipeline_runs_stage", "pipeline_runs", "stage IN ('COLLECT')"
    )
    op.drop_index(
        "ix_daily_selections_selection_date", table_name="daily_selections"
    )
    op.drop_table("daily_selections")
