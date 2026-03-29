"""Lightweight startup migrations for non-breaking schema/index updates."""

import logging

from sqlalchemy import text, inspect

from app.database import engine

logger = logging.getLogger(__name__)


def ensure_allowed_duplicate_products_table() -> None:
    """
    Create the allowed_duplicate_products table if it doesn't exist.
    Populate it with the initial 5 product types that were previously hardcoded.
    """
    try:
        with engine.begin() as conn:
            inspector = inspect(conn)
            
            # Check if table exists
            if "allowed_duplicate_products" not in inspector.get_table_names():
                logger.info("Creating allowed_duplicate_products table...")
                
                # Create the table
                conn.execute(text("""
                    CREATE TABLE allowed_duplicate_products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_type VARCHAR(100) NOT NULL UNIQUE,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        created_by INTEGER NOT NULL,
                        modified_at TIMESTAMP,
                        modified_by INTEGER,
                        FOREIGN KEY (created_by) REFERENCES users(id),
                        FOREIGN KEY (modified_by) REFERENCES users(id)
                    )
                """))
                
                # Create indexes
                conn.execute(text("""
                    CREATE INDEX idx_allowed_dup_product_type 
                    ON allowed_duplicate_products (product_type)
                """))
                
                conn.execute(text("""
                    CREATE INDEX idx_allowed_dup_is_active 
                    ON allowed_duplicate_products (is_active)
                """))
                
                logger.info("allowed_duplicate_products table created successfully")
                
                # Get the first superadmin user ID for created_by
                result = conn.execute(text("""
                    SELECT id FROM users WHERE user_role = 'superadmin' LIMIT 1
                """)).fetchone()
                
                if result:
                    superadmin_id = result[0]
                    
                    # Populate with initial 5 product types (previously hardcoded)
                    initial_products = [
                        "update",
                        "date down",
                        "gi clearing",
                        "schedule b",
                        "product delivery"
                    ]
                    
                    for product in initial_products:
                        conn.execute(text("""
                            INSERT INTO allowed_duplicate_products 
                            (product_type, is_active, created_by)
                            VALUES (:product_type, 1, :created_by)
                        """), {"product_type": product, "created_by": superadmin_id})
                    
                    logger.info(f"Populated {len(initial_products)} initial allowed duplicate product types")
                else:
                    logger.warning("No superadmin user found, skipping initial data population")
            else:
                logger.info("allowed_duplicate_products table already exists")
                
    except Exception as exc:
        logger.warning("Could not ensure allowed_duplicate_products table: %s", exc)


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
