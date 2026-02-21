"""Lightweight startup migrations for non-breaking schema/index updates."""

import logging

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)


def ensure_orders_file_product_team_index_non_unique() -> None:
    """
    Ensure idx_orders_file_product_team is non-unique.

    Business rule now allows duplicates for selected product types, so DB-level
    unique enforcement on (file_number, product_type, team_id) must be removed.
    """
    try:
        with engine.begin() as conn:
            dialect = conn.dialect.name

            if dialect == "sqlite":
                rows = conn.execute(text("PRAGMA index_list('orders')")).fetchall()
                has_index = False
                is_unique = False

                for row in rows:
                    if row[1] == "idx_orders_file_product_team":
                        has_index = True
                        is_unique = bool(row[2])
                        break

                if is_unique:
                    conn.execute(text("DROP INDEX IF EXISTS idx_orders_file_product_team"))
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_orders_file_product_team "
                            "ON orders (file_number, product_type, team_id)"
                        )
                    )
                    logger.info("Migrated idx_orders_file_product_team to non-unique (sqlite)")
                elif not has_index:
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_orders_file_product_team "
                            "ON orders (file_number, product_type, team_id)"
                        )
                    )
            else:
                row = conn.execute(
                    text(
                        """
                        SELECT indexdef
                        FROM pg_indexes
                        WHERE schemaname = ANY (current_schemas(false))
                          AND tablename = 'orders'
                          AND indexname = 'idx_orders_file_product_team'
                        """
                    )
                ).fetchone()

                if row and "UNIQUE INDEX" in row[0].upper():
                    conn.execute(text("DROP INDEX IF EXISTS idx_orders_file_product_team"))
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_orders_file_product_team "
                            "ON orders (file_number, product_type, team_id)"
                        )
                    )
                    logger.info("Migrated idx_orders_file_product_team to non-unique (postgres)")
                elif row is None:
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_orders_file_product_team "
                            "ON orders (file_number, product_type, team_id)"
                        )
                    )
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not ensure non-unique orders index: %s", exc)
