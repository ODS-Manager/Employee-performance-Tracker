"""
Run database migration: Rename employee_id to examiner_id
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the migration to rename employee_id to examiner_id"""
    engine = create_engine(str(settings.DATABASE_URL))
    
    try:
        with engine.connect() as conn:
            print("Running migration: Rename employee_id to examiner_id in users table...")
            
            # SQLite doesn't support renaming columns directly, so we need to check the schema
            # First, check if the column exists
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'employee_id' not in columns:
                print("❌ Column 'employee_id' not found in users table.")
                print(f"Available columns: {', '.join(columns)}")
                if 'examiner_id' in columns:
                    print("✅ Column 'examiner_id' already exists. Migration may have already been run.")
                return False
            
            if 'examiner_id' in columns:
                print("⚠️  Both 'employee_id' and 'examiner_id' columns exist. This is unexpected.")
                return False
            
            print("Found 'employee_id' column. Starting migration...")
            
            # For SQLite, we need to use ALTER TABLE to rename the column
            conn.execute(text("ALTER TABLE users RENAME COLUMN employee_id TO examiner_id"))
            
            # Drop old index if it exists
            try:
                conn.execute(text("DROP INDEX IF EXISTS idx_users_employee_id"))
                print("✅ Dropped old index 'idx_users_employee_id'")
            except Exception as e:
                print(f"⚠️  Could not drop old index: {e}")
            
            # Create new index
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_examiner_id ON users(examiner_id)"))
                print("✅ Created new index 'idx_users_examiner_id'")
            except Exception as e:
                print(f"⚠️  Could not create new index: {e}")
            
            conn.commit()
            
            print("✅ Migration completed successfully!")
            print("✅ Column 'employee_id' renamed to 'examiner_id' in users table")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
