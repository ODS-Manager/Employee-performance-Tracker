"""
Script to clean up duplicate organizations and consolidate to ORG-IND and ORG-VNM
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import SessionLocal
from app.models.organization import Organization

def cleanup_organizations():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("ORGANIZATION CLEANUP SCRIPT")
        print("=" * 70)
        
        # Get all organizations
        all_orgs = db.query(Organization).all()
        print(f"\nFound {len(all_orgs)} organizations:")
        for org in all_orgs:
            print(f"  ID: {org.id} | Code: {org.code:15s} | Name: {org.name}")
        
        # Find ORG-IND and ORG-VNM (the ones we want to keep)
        org_ind = db.query(Organization).filter(Organization.code == "ORG-IND").first()
        org_vnm = db.query(Organization).filter(Organization.code == "ORG-VNM").first()
        
        if not org_ind or not org_vnm:
            print("\n❌ ERROR: ORG-IND or ORG-VNM not found!")
            return
        
        print(f"\n✅ Target organizations:")
        print(f"  ORG-IND: ID {org_ind.id} - {org_ind.name}")
        print(f"  ORG-VNM: ID {org_vnm.id} - {org_vnm.name}")
        
        # Find old ODS-IND and ODS-VNM
        ods_ind = db.query(Organization).filter(Organization.code == "ODS-IND").first()
        ods_vnm = db.query(Organization).filter(Organization.code == "ODS-VNM").first()
        
        if ods_ind:
            print(f"\n🔄 Migrating data from ODS-IND (ID {ods_ind.id}) to ORG-IND (ID {org_ind.id})...")
            
            # Update users
            result = db.execute(
                text("UPDATE users SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_ind.id, "old_id": ods_ind.id}
            )
            print(f"  - Updated {result.rowcount} users")
            
            # Update teams
            result = db.execute(
                text("UPDATE teams SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_ind.id, "old_id": ods_ind.id}
            )
            print(f"  - Updated {result.rowcount} teams")
            
            # Update orders
            result = db.execute(
                text("UPDATE orders SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_ind.id, "old_id": ods_ind.id}
            )
            print(f"  - Updated {result.rowcount} orders")
            
            # Update quality audits
            result = db.execute(
                text("UPDATE quality_audits SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_ind.id, "old_id": ods_ind.id}
            )
            print(f"  - Updated {result.rowcount} quality audits")
            
            # Update attendance records
            result = db.execute(
                text("UPDATE attendance_records SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_ind.id, "old_id": ods_ind.id}
            )
            print(f"  - Updated {result.rowcount} attendance records")
            
            # Delete old organization
            db.delete(ods_ind)
            print(f"  ✅ Deleted ODS-IND organization")
        
        if ods_vnm:
            print(f"\n🔄 Migrating data from ODS-VNM (ID {ods_vnm.id}) to ORG-VNM (ID {org_vnm.id})...")
            
            # Update users
            result = db.execute(
                text("UPDATE users SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_vnm.id, "old_id": ods_vnm.id}
            )
            print(f"  - Updated {result.rowcount} users")
            
            # Update teams
            result = db.execute(
                text("UPDATE teams SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_vnm.id, "old_id": ods_vnm.id}
            )
            print(f"  - Updated {result.rowcount} teams")
            
            # Update orders
            result = db.execute(
                text("UPDATE orders SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_vnm.id, "old_id": ods_vnm.id}
            )
            print(f"  - Updated {result.rowcount} orders")
            
            # Update quality audits
            result = db.execute(
                text("UPDATE quality_audits SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_vnm.id, "old_id": ods_vnm.id}
            )
            print(f"  - Updated {result.rowcount} quality audits")
            
            # Update attendance records
            result = db.execute(
                text("UPDATE attendance_records SET org_id = :new_id WHERE org_id = :old_id"),
                {"new_id": org_vnm.id, "old_id": ods_vnm.id}
            )
            print(f"  - Updated {result.rowcount} attendance records")
            
            # Delete old organization
            db.delete(ods_vnm)
            print(f"  ✅ Deleted ODS-VNM organization")
        
        db.commit()
        
        # Final summary
        print("\n" + "=" * 70)
        print("FINAL STATUS")
        print("=" * 70)
        
        remaining_orgs = db.query(Organization).all()
        print(f"\nRemaining organizations ({len(remaining_orgs)}):")
        for org in remaining_orgs:
            user_count = db.execute(
                text("SELECT COUNT(*) FROM users WHERE org_id = :org_id"),
                {"org_id": org.id}
            ).scalar()
            team_count = db.execute(
                text("SELECT COUNT(*) FROM teams WHERE org_id = :org_id"),
                {"org_id": org.id}
            ).scalar()
            order_count = db.execute(
                text("SELECT COUNT(*) FROM orders WHERE org_id = :org_id"),
                {"org_id": org.id}
            ).scalar()
            
            print(f"\n  {org.code} (ID: {org.id}) - {org.name}")
            print(f"    Users: {user_count}, Teams: {team_count}, Orders: {order_count}")
        
        print("\n✅ Cleanup completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_organizations()
