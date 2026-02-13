#!/usr/bin/env python3
"""
Script to fix orgId=null issue for newly added users
All users with employee IDs EMP004-EMP151 should have orgId=2 (ORG-IND)
"""

import sqlite3
import sys

def main():
    conn = None
    # Connect to the database
    try:
        conn = sqlite3.connect('Backend/ods_development.db')
        cursor = conn.cursor()
        
        # First, let's see current state
        print("=== CURRENT STATE ===")
        cursor.execute("SELECT COUNT(*) FROM users WHERE org_id IS NULL;")
        null_count = cursor.fetchone()[0]
        print(f"Users with org_id=NULL: {null_count}")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = 1;")
        org1_count = cursor.fetchone()[0]
        print(f"Users with org_id=1 (ODS India): {org1_count}")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = 2;")
        org2_count = cursor.fetchone()[0]
        print(f"Users with org_id=2 (ORG-IND): {org2_count}")
        
        # Check which users have null org_id and their employee IDs
        cursor.execute("SELECT id, employee_id, user_name FROM users WHERE org_id IS NULL ORDER BY id;")
        null_users = cursor.fetchall()
        
        print(f"\nUsers with NULL org_id:")
        for user in null_users[:5]:  # Show first 5
            print(f"  ID: {user[0]}, Employee ID: {user[1]}, Username: {user[2]}")
        if len(null_users) > 5:
            print(f"  ... and {len(null_users) - 5} more")
        
        # Update all users with NULL org_id to have org_id=2
        # These should be all the EMP004-EMP151 users we added
        print(f"\n=== FIXING ORG IDS ===")
        cursor.execute("UPDATE users SET org_id = 2 WHERE org_id IS NULL;")
        updated_count = cursor.rowcount
        print(f"Updated {updated_count} users to have org_id=2")
        
        # Commit the changes
        conn.commit()
        
        # Verify the fix
        print(f"\n=== AFTER FIX ===")
        cursor.execute("SELECT COUNT(*) FROM users WHERE org_id IS NULL;")
        null_count_after = cursor.fetchone()[0]
        print(f"Users with org_id=NULL: {null_count_after}")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = 1;")
        org1_count_after = cursor.fetchone()[0]
        print(f"Users with org_id=1 (ODS India): {org1_count_after}")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = 2;")
        org2_count_after = cursor.fetchone()[0]
        print(f"Users with org_id=2 (ORG-IND): {org2_count_after}")
        
        cursor.execute("SELECT COUNT(*) FROM users;")
        total_count = cursor.fetchone()[0]
        print(f"Total users: {total_count}")
        
        print(f"\n✅ Successfully updated {updated_count} users!")
        print(f"Now all 152 users should be properly assigned to organizations.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        try:
            if conn:
                conn.close()
        except:
            pass

if __name__ == "__main__":
    main()