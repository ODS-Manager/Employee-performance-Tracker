#!/usr/bin/env python3
"""
Remove step start_time and end_time columns from orders table
"""
import sqlite3

DB_PATH = "ods_db.sqlite"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("REMOVING START/END TIME COLUMNS FROM ORDERS TABLE")
    print("=" * 80)
    
    # Step 1: Create new table without start/end time columns
    print("\n[1/5] Creating new orders table without start/end time columns...")
    cursor.execute("""
        CREATE TABLE orders_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_number VARCHAR(100) NOT NULL,
            entry_date DATE NOT NULL,
            transaction_type_id INTEGER NOT NULL,
            process_type_id INTEGER NOT NULL,
            order_status_id INTEGER NOT NULL,
            division_id INTEGER NOT NULL,
            state VARCHAR(5) NOT NULL,
            county VARCHAR(100) NOT NULL,
            product_type VARCHAR(100) NOT NULL,
            team_id INTEGER NOT NULL,
            org_id INTEGER NOT NULL,
            step1_user_id INTEGER,
            step1_fa_name_id INTEGER,
            step2_user_id INTEGER,
            step2_fa_name_id INTEGER,
            billing_status VARCHAR(20) CHECK (billing_status IN ('pending', 'done')),
            created_by INTEGER NOT NULL,
            modified_by INTEGER,
            deleted_at DATETIME,
            deleted_by INTEGER,
            created_at DATETIME,
            modified_at DATETIME,
            FOREIGN KEY (transaction_type_id) REFERENCES transaction_types(id),
            FOREIGN KEY (process_type_id) REFERENCES process_types(id),
            FOREIGN KEY (order_status_id) REFERENCES order_status(id),
            FOREIGN KEY (division_id) REFERENCES divisions(id),
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (org_id) REFERENCES organizations(id),
            FOREIGN KEY (step1_user_id) REFERENCES users(id),
            FOREIGN KEY (step2_user_id) REFERENCES users(id),
            FOREIGN KEY (step1_fa_name_id) REFERENCES fa_names(id),
            FOREIGN KEY (step2_fa_name_id) REFERENCES fa_names(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (modified_by) REFERENCES users(id),
            FOREIGN KEY (deleted_by) REFERENCES users(id)
        )
    """)
    print("  ✓ Created orders_new table")
    
    # Step 2: Copy data from old table to new table (excluding start/end time columns)
    print("\n[2/5] Copying data from old table to new table...")
    cursor.execute("""
        INSERT INTO orders_new (
            id, file_number, entry_date,
            transaction_type_id, process_type_id, order_status_id, division_id,
            state, county, product_type,
            team_id, org_id,
            step1_user_id, step1_fa_name_id,
            step2_user_id, step2_fa_name_id,
            billing_status,
            created_by, modified_by,
            deleted_at, deleted_by,
            created_at, modified_at
        )
        SELECT
            id, file_number, entry_date,
            transaction_type_id, process_type_id, order_status_id, division_id,
            state, county, product_type,
            team_id, org_id,
            step1_user_id, step1_fa_name_id,
            step2_user_id, step2_fa_name_id,
            billing_status,
            created_by, modified_by,
            deleted_at, deleted_by,
            created_at, modified_at
        FROM orders
    """)
    rows_copied = cursor.rowcount
    print(f"  ✓ Copied {rows_copied} orders")
    
    # Step 3: Drop old table
    print("\n[3/5] Dropping old orders table...")
    cursor.execute("DROP TABLE orders")
    print("  ✓ Dropped old table")
    
    # Step 4: Rename new table
    print("\n[4/5] Renaming orders_new to orders...")
    cursor.execute("ALTER TABLE orders_new RENAME TO orders")
    print("  ✓ Renamed table")
    
    # Step 5: Recreate indexes
    print("\n[5/5] Creating indexes...")
    cursor.execute("CREATE INDEX idx_orders_team_id ON orders(team_id)")
    cursor.execute("CREATE INDEX idx_orders_org_id ON orders(org_id)")
    cursor.execute("CREATE INDEX idx_orders_entry_date ON orders(entry_date)")
    cursor.execute("CREATE INDEX idx_orders_step1_user_id ON orders(step1_user_id)")
    cursor.execute("CREATE INDEX idx_orders_step2_user_id ON orders(step2_user_id)")
    cursor.execute("CREATE INDEX idx_orders_file_number ON orders(file_number)")
    cursor.execute("CREATE INDEX idx_orders_deleted_at ON orders(deleted_at)")
    print("  ✓ Created indexes")
    
    conn.commit()
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    cursor.execute("PRAGMA table_info(orders)")
    columns = cursor.fetchall()
    print(f"\nOrders table now has {len(columns)} columns:")
    for row in columns:
        print(f"  {row[0]:2d}. {row[1]:30s} {row[2]}")
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    print(f"\nTotal orders: {count}")
    
    # Check that no time columns exist
    has_time_columns = any('time' in col[1].lower() for col in columns if 'created_at' not in col[1] and 'modified_at' not in col[1] and 'deleted_at' not in col[1])
    if has_time_columns:
        print("\n❌ WARNING: Time columns still exist!")
    else:
        print("\n✓ SUCCESS: All start/end time columns removed!")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ COMPLETED: Removed all start/end time columns from orders table")
    print("=" * 80)

if __name__ == "__main__":
    main()
