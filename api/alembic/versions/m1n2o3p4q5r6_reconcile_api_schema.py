"""Reconcile API-owned schema and use exact money types.

Revision ID: m1n2o3p4q5r6
Revises: k1a2b3c4d5e6
Create Date: 2026-07-23
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m1n2o3p4q5r6"
down_revision: Union[str, Sequence[str], None] = "k1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _constraint(table: str, name: str, definition: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = '{name}'
                  AND conrelid = 'public.{table}'::regclass
            ) THEN
                ALTER TABLE public.{table}
                ADD CONSTRAINT {name} {definition};
            END IF;
        END
        $$;
        """
    )


def _configure_supabase_rls() -> None:
    """Add Data API grants and ownership policies when Supabase Auth is present."""
    op.execute("ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.price_alerts ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated')
               AND to_regprocedure('auth.uid()') IS NOT NULL THEN
                GRANT SELECT, INSERT, UPDATE, DELETE
                    ON public.user_preferences, public.price_alerts
                    TO authenticated;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename = 'user_preferences'
                      AND policyname = 'user_preferences_owner'
                ) THEN
                    CREATE POLICY user_preferences_owner
                    ON public.user_preferences
                    FOR ALL
                    TO authenticated
                    USING ((SELECT auth.uid()) = user_id)
                    WITH CHECK ((SELECT auth.uid()) = user_id);
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename = 'price_alerts'
                      AND policyname = 'price_alerts_owner'
                ) THEN
                    CREATE POLICY price_alerts_owner
                    ON public.price_alerts
                    FOR ALL
                    TO authenticated
                    USING ((SELECT auth.uid()) = user_id)
                    WITH CHECK ((SELECT auth.uid()) = user_id);
                END IF;
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    ingestion_columns = {
        column["name"] for column in inspector.get_columns("ingestion_runs")
    }
    if "error_message" not in ingestion_columns:
        op.add_column(
            "ingestion_runs",
            sa.Column("error_message", sa.Text(), nullable=True),
        )

    op.alter_column(
        "prices",
        "price_nzd",
        type_=sa.Numeric(10, 2),
        postgresql_using="round(price_nzd::numeric, 2)",
        existing_nullable=False,
    )
    op.alter_column(
        "prices",
        "promo_price_nzd",
        type_=sa.Numeric(10, 2),
        postgresql_using="round(promo_price_nzd::numeric, 2)",
        existing_nullable=True,
    )
    op.alter_column(
        "prices",
        "currency",
        existing_type=sa.String(length=3),
        existing_server_default=sa.text("'NZD'::character varying"),
        nullable=False,
    )
    op.alter_column(
        "price_history",
        "price_nzd",
        type_=sa.Numeric(10, 2),
        postgresql_using="round(price_nzd::numeric, 2)",
        existing_nullable=False,
    )
    op.alter_column(
        "price_history",
        "promo_price_nzd",
        type_=sa.Numeric(10, 2),
        postgresql_using="round(promo_price_nzd::numeric, 2)",
        existing_nullable=True,
    )

    _constraint("prices", "ck_price_positive", "CHECK (price_nzd > 0)")
    _constraint(
        "prices",
        "ck_promo_price_positive",
        "CHECK (promo_price_nzd IS NULL OR promo_price_nzd > 0)",
    )
    _constraint(
        "price_history",
        "ck_price_history_positive",
        "CHECK (price_nzd > 0)",
    )
    _constraint(
        "price_history",
        "ck_price_history_promo_positive",
        "CHECK (promo_price_nzd IS NULL OR promo_price_nzd > 0)",
    )

    existing_tables = set(inspector.get_table_names())
    if "user_preferences" not in existing_tables:
        op.create_table(
            "user_preferences",
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("default_lat", sa.Float(), nullable=True),
            sa.Column("default_lng", sa.Float(), nullable=True),
            sa.Column(
                "default_radius_km",
                sa.Float(),
                nullable=False,
                server_default=sa.text("2.0"),
            ),
            sa.Column(
                "preferred_stores",
                postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                nullable=False,
                server_default=sa.text("'{}'::uuid[]"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "(default_lat IS NULL AND default_lng IS NULL) OR "
                "(default_lat IS NOT NULL AND default_lng IS NOT NULL "
                "AND default_lat BETWEEN -47 AND -34 "
                "AND default_lng BETWEEN 165 AND 179)",
                name="ck_user_preferences_location",
            ),
            sa.CheckConstraint(
                "default_radius_km BETWEEN 1 AND 10",
                name="ck_user_preferences_radius",
            ),
        )

    if "price_alerts" not in existing_tables:
        op.create_table(
            "price_alerts",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "product_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("products.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("threshold_price", sa.Numeric(10, 2), nullable=True),
            sa.Column(
                "alert_on_promo",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_notified_price", sa.Numeric(10, 2), nullable=True),
            sa.Column(
                "active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "threshold_price IS NOT NULL OR alert_on_promo",
                name="ck_price_alert_has_condition",
            ),
            sa.CheckConstraint(
                "threshold_price IS NULL OR threshold_price > 0",
                name="ck_price_alert_threshold_positive",
            ),
        )

    # Re-inspect in case either table was created above or already existed
    # outside Alembic, then converge indexes and constraints.
    inspector = sa.inspect(bind)
    preference_columns = {
        column["name"] for column in inspector.get_columns("user_preferences")
    }
    if "preferred_stores" not in preference_columns:
        op.add_column(
            "user_preferences",
            sa.Column(
                "preferred_stores",
                postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                nullable=False,
                server_default=sa.text("'{}'::uuid[]"),
            ),
        )

    # Recreate this constraint so manually provisioned tables also receive the
    # explicit non-null branch. PostgreSQL CHECK constraints accept UNKNOWN,
    # so bounds alone would otherwise permit a half-populated location.
    op.execute(
        """
        ALTER TABLE public.user_preferences
        DROP CONSTRAINT IF EXISTS ck_user_preferences_location;
        ALTER TABLE public.user_preferences
        ADD CONSTRAINT ck_user_preferences_location
        CHECK (
            (default_lat IS NULL AND default_lng IS NULL)
            OR (
                default_lat IS NOT NULL
                AND default_lng IS NOT NULL
                AND default_lat BETWEEN -47 AND -34
                AND default_lng BETWEEN 165 AND 179
            )
        );
        """
    )

    alert_columns = {
        column["name"] for column in inspector.get_columns("price_alerts")
    }
    missing_alert_columns = {
        "last_notified_price": sa.Column(
            "last_notified_price", sa.Numeric(10, 2), nullable=True
        ),
        "updated_at": sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    }
    for name, column in missing_alert_columns.items():
        if name not in alert_columns:
            op.add_column("price_alerts", column)

    _constraint(
        "price_alerts",
        "ck_price_alert_has_condition",
        "CHECK (threshold_price IS NOT NULL OR alert_on_promo)",
    )
    _constraint(
        "price_alerts",
        "ck_price_alert_threshold_positive",
        "CHECK (threshold_price IS NULL OR threshold_price > 0)",
    )

    alert_indexes = {
        index["name"] for index in inspector.get_indexes("price_alerts")
    }
    if "ix_price_alert_user_active" not in alert_indexes:
        op.create_index(
            "ix_price_alert_user_active",
            "price_alerts",
            ["user_id", "active"],
        )
    if "ix_price_alert_product_active" not in alert_indexes:
        op.create_index(
            "ix_price_alert_product_active",
            "price_alerts",
            ["product_id", "active"],
        )

    # Enforce the active-alert limit atomically for every write path. The
    # transaction-scoped advisory lock serializes concurrent writes per user.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.enforce_active_price_alert_limit()
        RETURNS trigger
        LANGUAGE plpgsql
        SET search_path = public, pg_temp
        AS $$
        BEGIN
            IF NEW.active THEN
                PERFORM pg_advisory_xact_lock(
                    hashtextextended(NEW.user_id::text, 0)
                );
                IF (
                    SELECT count(*)
                    FROM public.price_alerts
                    WHERE user_id = NEW.user_id
                      AND active
                      AND id IS DISTINCT FROM NEW.id
                ) >= 10 THEN
                    RAISE EXCEPTION
                        'A user may have at most 10 active price alerts'
                        USING ERRCODE = 'check_violation',
                              CONSTRAINT = 'ck_price_alert_active_limit';
                END IF;
            END IF;
            RETURN NEW;
        END
        $$;

        REVOKE ALL
            ON FUNCTION public.enforce_active_price_alert_limit()
            FROM PUBLIC;

        DROP TRIGGER IF EXISTS trg_price_alert_active_limit
            ON public.price_alerts;
        CREATE TRIGGER trg_price_alert_active_limit
            BEFORE INSERT OR UPDATE OF active, user_id
            ON public.price_alerts
            FOR EACH ROW
            EXECUTE FUNCTION public.enforce_active_price_alert_limit();
        """
    )

    _configure_supabase_rls()

    op.create_table(
        "ingestion_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("chain", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_ingestion_job_status",
        ),
    )
    op.create_index(
        "ix_ingestion_job_status_created",
        "ingestion_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "uq_ingestion_job_active_chain",
        "ingestion_jobs",
        ["chain"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.execute("ALTER TABLE public.ingestion_jobs ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                REVOKE ALL ON public.ingestion_jobs FROM anon;
            END IF;
            IF EXISTS (
                SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'
            ) THEN
                REVOKE ALL ON public.ingestion_jobs FROM authenticated;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.execute(
        """
        DROP POLICY IF EXISTS price_alerts_owner ON public.price_alerts;
        DROP POLICY IF EXISTS user_preferences_owner ON public.user_preferences;
        DROP TRIGGER IF EXISTS trg_price_alert_active_limit
            ON public.price_alerts;
        DROP FUNCTION IF EXISTS public.enforce_active_price_alert_limit();
        """
    )
    op.drop_table("price_alerts")
    op.drop_table("user_preferences")

    op.drop_constraint(
        "ck_price_history_promo_positive", "price_history", type_="check"
    )
    op.drop_constraint(
        "ck_price_history_positive", "price_history", type_="check"
    )
    op.drop_constraint("ck_promo_price_positive", "prices", type_="check")
    op.drop_constraint("ck_price_positive", "prices", type_="check")

    op.alter_column(
        "price_history",
        "promo_price_nzd",
        type_=sa.Float(),
        postgresql_using="promo_price_nzd::double precision",
        existing_nullable=True,
    )
    op.alter_column(
        "price_history",
        "price_nzd",
        type_=sa.Float(),
        postgresql_using="price_nzd::double precision",
        existing_nullable=False,
    )
    op.alter_column(
        "prices",
        "promo_price_nzd",
        type_=sa.Float(),
        postgresql_using="promo_price_nzd::double precision",
        existing_nullable=True,
    )
    op.alter_column(
        "prices",
        "price_nzd",
        type_=sa.Float(),
        postgresql_using="price_nzd::double precision",
        existing_nullable=False,
    )
    op.drop_column("ingestion_runs", "error_message")
