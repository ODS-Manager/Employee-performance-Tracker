"""
Script to remove duplicate organizations
- Migrates users from Org 1 to Org 3 (ODS - India)
- Deletes duplicate organizations: Org 1 (ODS India), Org 2 (ODS Vietnam), Org 4 (ODS - Vietnam)
- Keeps: Org 3 (ODS - India) which has all the real data
"""
import sqlite3
import sys

DB_PATH = '/home/buddy/Work/ODS/Employee-performance-Tracker/Backend/ods_db.sqlite'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== Removing Duplicate Organizations ===\n")
    
    # Step 1: Migrate users from Org 1 to Org 3
    print("Step 1: Migrating users from Org 1 (ODS India) to Org 3 (ODS - India)...")
    cursor.execute('SELECT id, user_name FROM users WHERE org_id = 1')
    users_to_migrate = cursor.fetchall()
    
    for user_id, username in users_to_migrate:
        print(f"  - Migrating user {user_id} ({username}) from Org 1 to Org 3")
        cursor.execute('UPDATE users SET org_id = 3 WHERE id = ?', (user_id,))
    
    print(f"  ✓ Migrated {len(users_to_migrate)} users\n")
    
    # Step 2: Check if any data still references the duplicate orgs
    print("Step 2: Checking for remaining references...")
    for org_id, org_name in [(1, 'ODS India'), (2, 'ODS Vietnam'), (4, 'ODS - Vietnam')]:
        cursor.execute('SELECT COUNT(*) FROM teams WHERE org_id = ?', (org_id,))
        teams = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE org_id = ?', (org_id,))
        users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM orders WHERE org_id = ?', (org_id,))
        orders = cursor.fetchone()[0]
        
        if teams > 0 or users > 0 or orders > 0:
            print(f"  ⚠ Org {org_id} ({org_name}) still has data: {teams} teams, {users} users, {orders} orders")
            print("  Cannot delete - please migrate data first")
            return
        else:
            print(f"  ✓ Org {org_id} ({org_name}) has no data")
    
    print()
    
    # Step 3: Delete duplicate organizations
    print("Step 3: Deleting duplicate organizations...")
    for org_id, org_name in [(1, 'ODS India'), (2, 'ODS Vietnam'), (4, 'ODS - Vietnam')]:
        print(f"  - Deleting Org {org_id} ({org_name})")
        cursor.execute('DELETE FROM organizations WHERE id = ?', (org_id,))
    
    print("  ✓ Deleted 3 duplicate organizations\n")
    
    # Step 4: Verify final state
    print("Step 4: Verifying final state...")
    cursor.execute('SELECT id, name FROM organizations ORDER BY id')
    remaining_orgs = cursor.fetchall()
    
    print(f"  Remaining organizations:")
    for org_id, org_name in remaining_orgs:
        cursor.execute('SELECT COUNT(*) FROM teams WHERE org_id = ?', (org_id,))
        teams = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE org_id = ?', (org_id,))
        users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM orders WHERE org_id = ?', (org_id,))
        orders = cursor.fetchone()[0]
        
        print(f"    - Org {org_id} ({org_name}): {teams} teams, {users} users, {orders} orders")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✓ Successfully removed duplicate organizations!")
    print("  Kept: Org 3 (ODS - India) with all data")
    print("  Deleted: Org 1 (ODS India), Org 2 (ODS Vietnam), Org 4 (ODS - Vietnam)")

if __name__ == '__main__':
    main()
