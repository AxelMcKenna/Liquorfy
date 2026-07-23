"""Add leases, retries, cancellation, and schedule deduplication to ingestion jobs.

Revision ID: n1o2p3q4r5s6
Revises: m1n2o3p4q5r6
Create Date: 2026-07-23
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "n1o2p3q4r5s6"
down_revision: Union[str, Sequence[str], None] = "m1n2o3p4q5r6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ingestion_jobs",
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2"),
        ),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("claimed_by", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.drop_constraint(
        "ck_ingestion_job_status",
        "ingestion_jobs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_ingestion_job_status",
        "ingestion_jobs",
        "status IN ('queued', 'running', 'completed', 'failed', 'cancelled')",
    )
    op.create_check_constraint(
        "ck_ingestion_job_attempt_count",
        "ingestion_jobs",
        "attempt_count >= 0 AND attempt_count <= max_attempts",
    )
    op.create_check_constraint(
        "ck_ingestion_job_max_attempts",
        "ingestion_jobs",
        "max_attempts BETWEEN 1 AND 10",
    )

    op.drop_index(
        "ix_ingestion_job_status_created",
        table_name="ingestion_jobs",
    )
    op.create_index(
        "ix_ingestion_job_ready",
        "ingestion_jobs",
        ["available_at", "created_at"],
        postgresql_where=sa.text("status = 'queued'"),
    )
    op.create_index(
        "ix_ingestion_job_expired_lease",
        "ingestion_jobs",
        ["lease_expires_at"],
        postgresql_where=sa.text("status = 'running'"),
    )
    op.create_index(
        "uq_ingestion_job_dedupe_key",
        "ingestion_jobs",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE ingestion_jobs
        SET status = 'failed',
            finished_at = COALESCE(finished_at, now()),
            error_message = COALESCE(
                error_message,
                'Cancelled job converted during migration downgrade'
            )
        WHERE status = 'cancelled'
        """
    )

    op.drop_index(
        "uq_ingestion_job_dedupe_key",
        table_name="ingestion_jobs",
    )
    op.drop_index(
        "ix_ingestion_job_expired_lease",
        table_name="ingestion_jobs",
    )
    op.drop_index(
        "ix_ingestion_job_ready",
        table_name="ingestion_jobs",
    )
    op.create_index(
        "ix_ingestion_job_status_created",
        "ingestion_jobs",
        ["status", "created_at"],
    )

    op.drop_constraint(
        "ck_ingestion_job_max_attempts",
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        "ck_ingestion_job_attempt_count",
        "ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        "ck_ingestion_job_status",
        "ingestion_jobs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_ingestion_job_status",
        "ingestion_jobs",
        "status IN ('queued', 'running', 'completed', 'failed')",
    )

    for column in (
        "cancel_requested_at",
        "lease_expires_at",
        "heartbeat_at",
        "claimed_by",
        "max_attempts",
        "attempt_count",
        "available_at",
        "scheduled_for",
        "dedupe_key",
    ):
        op.drop_column("ingestion_jobs", column)
