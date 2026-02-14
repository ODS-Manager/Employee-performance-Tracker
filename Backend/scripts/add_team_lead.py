"""
Add Team Lead User Script
Adds a team lead user to complete the 4 user types
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.core.security import get_password_hash
from datetime import datetime


def add_team_lead():
    """Add a team lead user"""
    db = SessionLocal()
    
    try:
        # Check if ODS-IND exists
        org_ind = db.query(Organization).filter(Organization.code == "ODS-IND").first()
        
        if not org_ind:
            print("ERROR: Organization 'ODS-IND' not found in database")
            return False
        
        print(f"Found organization: {org_ind.name} (ID: {org_ind.id}, Code: {org_ind.code})")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.user_name == "teamlead_ods_ind").first()
        if existing_user:
            print("User 'teamlead_ods_ind' already exists!")
            print(f"Username: teamlead_ods_ind")
            print(f"Password: TeamLeadOdsInd123!")
            print(f"Role: {existing_user.user_role}")
            print(f"Org ID: {existing_user.org_id}")
            print(f"Employee ID: {existing_user.employee_id}")
            return True
        
        # Create team lead user
        user = User(
            user_name="teamlead_ods_ind",
            password_hash=get_password_hash("TeamLeadOdsInd123!"),
            employee_id="TL001",
            user_role="TEAM_LEAD",
            org_id=org_ind.id,
            is_active=True,
            must_change_password=False,
            token_version=0,
            password_last_changed=datetime.utcnow(),
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        
        print("\nSuccessfully created team lead user:")
        print("-" * 80)
        print(f"Username: teamlead_ods_ind")
        print(f"Password: TeamLeadOdsInd123!")
        print(f"Role: TEAM_LEAD")
        print(f"Org ID: {org_ind.id}")
        print(f"Employee ID: TL001")
        print("-" * 80)
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("ADD TEAM LEAD USER SCRIPT")
    print("=" * 80)
    print("\nAdding team lead user...")
    success = add_team_lead()
    if success:
        print("\n✓ Team lead user added successfully!")
    else:
        print("\n✗ Failed to add team lead user!")
        sys.exit(1)
