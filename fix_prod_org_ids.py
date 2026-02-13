#!/usr/bin/env python3
"""
Script to fix orgId=null issue in production database
All users with null org_id should have orgId=2 (ORG-IND)
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set production database URL
# This should match the production Cloud SQL connection
DATABASE_URL = "postgresql://ods_user:ods123@/ods_db?host=/cloudsql/project-0990a5d7-310c-4a56-837:asia-south1:ods-database"

def main():
    try:
        print("=== CONNECTING TO PRODUCTION DATABASE ===")
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
            }
        )
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            print("✅ Connected to production database!")
            
            # Check current state
            print("\n=== CURRENT STATE ===")
            
            result = session.execute(text("""
                SELECT 
                    CASE 
                        WHEN org_id IS NULL THEN 'NULL'
                        ELSE CAST(org_id AS TEXT)
                    END as org_id,
                    COUNT(*) as user_count
                FROM users 
                GROUP BY org_id 
                ORDER BY org_id
            """))
            
            for row in result:
                print(f"org_id={row.org_id}: {row.user_count} users")
            
            # Show sample users with null org_id
            result = session.execute(text("""
                SELECT id, employee_id, user_name, org_id 
                FROM users 
                WHERE org_id IS NULL 
                LIMIT 5
            """))
            
            null_users = result.fetchall()
            if null_users:
                print(f"\n❌ Found {len(null_users)} users with NULL org_id (showing first 5):")
                for user in null_users:
                    print(f"  ID: {user.id}, Employee ID: {user.employee_id}, Username: {user.user_name}")
                
                # Update all users with NULL org_id to have org_id=2
                print(f"\n=== FIXING ORG IDS ===")
                result = session.execute(text("""
                    UPDATE users 
                    SET org_id = 2, modified_at = NOW()
                    WHERE org_id IS NULL
                """))
                
                updated_count = result.rowcount
                session.commit()
                print(f"✅ Updated {updated_count} users to have org_id=2")
                
                # Verify the fix
                print(f"\n=== AFTER FIX ===")
                result = session.execute(text("""
                    SELECT 
                        CASE 
                            WHEN org_id IS NULL THEN 'NULL'
                            ELSE CAST(org_id AS TEXT)
                        END as org_id,
                        COUNT(*) as user_count
                    FROM users 
                    GROUP BY org_id 
                    ORDER BY org_id
                """))
                
                for row in result:
                    print(f"org_id={row.org_id}: {row.user_count} users")
                
                # Show total
                result = session.execute(text("SELECT COUNT(*) as total FROM users"))
                total = result.fetchone().total
                print(f"Total users: {total}")
                
            else:
                print(f"\n✅ No users with NULL org_id found - already fixed!")
                
                # Still show totals
                result = session.execute(text("SELECT COUNT(*) as total FROM users"))
                total = result.fetchone().total
                print(f"Total users: {total}")
            
    except Exception as e:
        print(f"❌ Error connecting to production database: {e}")
        print(f"This script needs to be run from the production Cloud Run environment")
        print(f"or with proper Cloud SQL proxy connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()