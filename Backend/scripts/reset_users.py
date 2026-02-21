"""
Database User Reset Script
Removes all users and creates 3 test users:
1. superadmin (SUPERADMIN role)
2. admin_ods_ind (ADMIN role for ODS-IND)
3. employee_ods_ind (EMPLOYEE role for ODS-IND)
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
from sqlalchemy import text


def reset_users():
    """Reset all users and create 3 test users"""
    db = SessionLocal()
    
    try:
        # First, check if ODS-IND exists
        org_ind = db.query(Organization).filter(Organization.code == "ODS-IND").first()
        
        if not org_ind:
            print("ERROR: Organization 'ODS-IND' not found in database")
            print("Please create the organization first")
            return False
        
        print(f"Found organization: {org_ind.name} (ID: {org_ind.id}, Code: {org_ind.code})")
        
        # Delete all existing users
        deleted_count = db.query(User).delete()
        db.commit()
        print(f"Deleted {deleted_count} existing users")
        
        # Create 3 test users
        users_to_create = [
            {
                "user_name": "superadmin",
                "password": "SuperAdmin123!",
                "examiner_id": "SA001",
                "user_role": "SUPERADMIN",
                "org_id": None,  # Superadmin has no org
                "is_active": True,
                "must_change_password": False,
                "token_version": 0
            },
            {
                "user_name": "admin_ods_ind",
                "password": "AdminOdsInd123!",
                "examiner_id": "A001",
                "user_role": "ADMIN",
                "org_id": org_ind.id,
                "is_active": True,
                "must_change_password": False,
                "token_version": 0
            },
            {
                "user_name": "employee_ods_ind",
                "password": "EmployeeOdsInd123!",
                "examiner_id": "E001",
                "user_role": "EMPLOYEE",
                "org_id": org_ind.id,
                "is_active": True,
                "must_change_password": False,
                "token_version": 0
            }
        ]
        
        created_users = []
        for user_data in users_to_create:
            password = user_data.pop("password")
            user = User(
                **user_data,
                password_hash=get_password_hash(password),
                password_last_changed=datetime.utcnow(),
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow()
            )
            db.add(user)
            created_users.append((user_data["user_name"], password))
        
        db.commit()
        
        print(f"\nSuccessfully created {len(created_users)} users:")
        print("-" * 80)
        for username, password in created_users:
            user = db.query(User).filter(User.user_name == username).first()
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"Role: {user.user_role}")
            print(f"Org ID: {user.org_id}")
            print(f"Employee ID: {user.examiner_id}")
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
    print("DATABASE USER RESET SCRIPT")
    print("=" * 80)
    print("\nThis will DELETE ALL USERS and create 3 test users")
    print("Are you sure you want to continue? (yes/no): ", end="")
    
    response = input().strip().lower()
    
    if response == "yes":
        print("\nProceeding with user reset...")
        success = reset_users()
        if success:
            print("\n✓ User reset completed successfully!")
        else:
            print("\n✗ User reset failed!")
            sys.exit(1)
    else:
        print("\nOperation cancelled.")
        sys.exit(0)
