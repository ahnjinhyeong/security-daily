"""Create pipeline_runs table.

Revision ID: 0002_create_pipeline_runs
Revises: 0001_create_articles
Create Date: 2026-08-19
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_create_pipeline_runs"
down_revision: str | Sequence[str] | None = "0001_create_articles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawled_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_type", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')",
            name="ck_pipeline_runs_status",
        ),
        sa.CheckConstraint("stage IN ('COLLECT')", name="ck_pipeline_runs_stage"),
        sa.CheckConstraint(
            "crawled_count >= 0 AND saved_count >= 0 AND duplicate_count >= 0",
            name="ck_pipeline_runs_counts_nonnegative",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pipeline_runs_target_date", "pipeline_runs", ["target_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_pipeline_runs_target_date", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")

