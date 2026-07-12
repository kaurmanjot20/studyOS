"""create interview_sessions table

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-12
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company", sa.String(length=120), nullable=True),
        sa.Column("subject", sa.String(length=160), nullable=True),
        sa.Column("difficulty", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("target_questions", sa.Integer(), server_default="5", nullable=False),
        sa.Column("asked_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("transcript", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_interview_sessions_workspace_id", "interview_sessions", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("interview_sessions")
