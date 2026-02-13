"""
Script to initialize the database with tables, organizations, and test users
"""
from app.database import engine, SessionLocal
from app.models.user import Base, User, UserRole
from app.models.organization import Organization
from app.core.security import get_password_hash
from datetime import datetime

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created successfully!")

def create_organizations():
    """Create organizations (ODS-IND and ODS-VNM)"""
    db = SessionLocal()
    try:
        # Check if organizations already exist
        existing_orgs = db.query(Organization).count()
        if existing_orgs > 0:
            print(f"[OK] Database already has {existing_orgs} organizations. Skipping organization creation.")
            return db.query(Organization).all()

        print("\nCreating organizations...")
        
        # Create ODS-IND organization
        ods_ind = Organization(
            name="ODS - IND",
            code="IND",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(ods_ind)
        print("[OK] Created organization: ODS - IND (code: IND)")

        # Create ODS-VNM organization
        ods_vnm = Organization(
            name="ODS - VNM",
            code="VNM",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(ods_vnm)
        print("[OK] Created organization: ODS - VNM (code: VNM)")

        db.commit()
        print("\n[SUCCESS] Organizations created successfully!")
        
        # Return the created organizations
        return db.query(Organization).all()

    except Exception as e:
        print(f"\n[ERROR] Error creating organizations: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return []
    finally:
        db.close()


def create_test_users():
    """Create test users for each role"""
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"[OK] Database already has {existing_users} users. Skipping user creation.")
            return

        # Get ODS-IND organization (should exist after create_organizations)
        ods_ind_org = db.query(Organization).filter(Organization.code == "IND").first()
        if not ods_ind_org:
            print("[ERROR] ODS-IND organization not found. Cannot create users.")
            return

        print("\nCreating test users...")
        
        # Test user passwords
        passwords = {
            "admin": "admin123",
            "lead": "lead123",
            "emp": "emp123"
        }
        
        # Superadmin user (no org_id needed)
        admin = User(
            user_name="admin",
            employee_id="EMP001",
            password_hash=get_password_hash(passwords["admin"]),
            user_role=UserRole.SUPERADMIN,  # Changed to SUPERADMIN
            org_id=None,  # Superadmin has no org restriction
            is_active=True
        )
        db.add(admin)
        print(f"[OK] Created superadmin user: admin / {passwords['admin']}")

        # Team lead user (assign to ODS-IND)
        teamlead = User(
            user_name="teamlead",
            employee_id="EMP002",
            password_hash=get_password_hash(passwords["lead"]),
            user_role=UserRole.TEAM_LEAD,
            org_id=ods_ind_org.id,
            is_active=True
        )
        db.add(teamlead)
        print(f"[OK] Created team lead user: teamlead / {passwords['lead']} (org: {ods_ind_org.name})")

        # Employee user (assign to ODS-IND)
        employee = User(
            user_name="employee",
            employee_id="EMP003",
            password_hash=get_password_hash(passwords["emp"]),
            user_role=UserRole.EMPLOYEE,
            org_id=ods_ind_org.id,
            is_active=True
        )
        db.add(employee)
        print(f"[OK] Created employee user: employee / {passwords['emp']} (org: {ods_ind_org.name})")

        db.commit()
        print("\n[SUCCESS] Test users created successfully!")
        print("\nYou can now login with:")
        print(f"  Superadmin: admin / {passwords['admin']} (can manage all orgs)")
        print(f"  Team Lead:  teamlead / {passwords['lead']} (ODS-IND)")
        print(f"  Employee:   employee / {passwords['emp']} (ODS-IND)")

    except Exception as e:
        print(f"\n[ERROR] Error creating test users: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    
    init_db()
    create_organizations()
    create_test_users()
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Database initialization complete!")
    print("=" * 60)
