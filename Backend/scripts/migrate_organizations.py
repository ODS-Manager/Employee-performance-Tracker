"""
Organization Migration Script
Consolidates 4 organizations into 2:
- Merges ODS-IND (ID 1) data into ORG-IND (ID 3)
- Deletes empty ODS-VNM (ID 2)
- Keeps ORG-IND (ID 3) and ORG-VNM (ID 4)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from sqlalchemy import text


def migrate_organizations():
    """Migrate old organizations to new ones"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("ORGANIZATION MIGRATION")
        print("=" * 80)
        
        # Step 1: Migrate ODS-IND (ID 1) data to ORG-IND (ID 3)
        print("\n[1/7] Migrating users from ODS-IND to ORG-IND...")
        result = db.execute(text("UPDATE users SET org_id = 3 WHERE org_id = 1"))
        print(f"  ✓ Migrated {result.rowcount} users")
        db.commit()
        
        print("\n[2/7] Migrating teams from ODS-IND to ORG-IND...")
        result = db.execute(text("UPDATE teams SET org_id = 3 WHERE org_id = 1"))
        print(f"  ✓ Migrated {result.rowcount} teams")
        db.commit()
        
        print("\n[3/7] Migrating orders from ODS-IND to ORG-IND...")
        result = db.execute(text("UPDATE orders SET org_id = 3 WHERE org_id = 1"))
        print(f"  ✓ Migrated {result.rowcount} orders")
        db.commit()
        
        print("\n[4/7] Migrating quality_audits from ODS-IND to ORG-IND...")
        result = db.execute(text("UPDATE quality_audits SET org_id = 3 WHERE org_id = 1"))
        print(f"  ✓ Migrated {result.rowcount} quality audits")
        db.commit()
        
        print("\n[5/7] Migrating attendance_records from ODS-IND to ORG-IND...")
        result = db.execute(text("UPDATE attendance_records SET org_id = 3 WHERE org_id = 1"))
        print(f"  ✓ Migrated {result.rowcount} attendance records")
        db.commit()
        
        print("\n[6/7] Migrating performance metrics from ODS-IND to ORG-IND...")
        result1 = db.execute(text("UPDATE employee_performance_metrics SET org_id = 3 WHERE org_id = 1"))
        result2 = db.execute(text("UPDATE team_performance_metrics SET org_id = 3 WHERE org_id = 1"))
        print(f"  ✓ Migrated {result1.rowcount} employee metrics and {result2.rowcount} team metrics")
        db.commit()
        
        # Step 2: Delete old organizations
        print("\n[7/7] Deleting old organizations...")
        
        # Check if ODS-IND still has any data
        check = db.execute(text("SELECT COUNT(*) FROM users WHERE org_id = 1")).scalar()
        if check > 0:
            print(f"  ⚠ WARNING: ODS-IND still has {check} users. Cannot delete.")
            return False
        
        # Delete ODS-IND and ODS-VNM
        result = db.execute(text("DELETE FROM organizations WHERE id IN (1, 2)"))
        print(f"  ✓ Deleted {result.rowcount} old organizations (ODS-IND, ODS-VNM)")
        db.commit()
        
        # Verify final state
        print("\n" + "=" * 80)
        print("FINAL STATE")
        print("=" * 80)
        
        orgs = db.execute(text("""
            SELECT 
                o.id,
                o.code,
                o.name,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(DISTINCT t.id) as team_count,
                COUNT(DISTINCT ord.id) as order_count
            FROM organizations o
            LEFT JOIN users u ON u.org_id = o.id
            LEFT JOIN teams t ON t.org_id = o.id
            LEFT JOIN orders ord ON ord.org_id = o.id
            GROUP BY o.id, o.code, o.name
            ORDER BY o.id
        """)).fetchall()
        
        for org in orgs:
            print(f"\n{org.code} - {org.name}")
            print(f"  Users: {org.user_count}")
            print(f"  Teams: {org.team_count}")
            print(f"  Orders: {org.order_count}")
        
        print("\n" + "=" * 80)
        print("✓ Migration completed successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate_organizations()
    sys.exit(0 if success else 1)
