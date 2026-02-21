#!/usr/bin/env python3
"""
Import data from CSV files into the database
"""

import sys
import os
import csv
from datetime import datetime

# Add the backend to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, Base
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.team import Team, TeamState, TeamProduct
from app.models.user_team import UserTeam
from app.models.fa_name import FAName
from app.models.team_fa_name import TeamFAName

# Default password for all users
DEFAULT_PASSWORD = "Test@123"

def parse_comma_separated(value):
    """Parse comma-separated values and return as list"""
    if not value:
        return []
    # Split by comma and strip whitespace
    return [item.strip() for item in value.split(',') if item.strip()]

def normalize_username(name):
    """Convert name to lowercase alphanumeric username"""
    normalized = ''.join(ch.lower() for ch in name if ch.isalnum())
    return normalized or 'user'

def generate_unique_username(base_username, used_usernames):
    """Generate unique username by adding numeric suffix if needed"""
    if base_username not in used_usernames:
        used_usernames.add(base_username)
        return base_username

    suffix = 2
    while True:
        candidate = f"{base_username}_{suffix}"
        if candidate not in used_usernames:
            used_usernames.add(candidate)
            return candidate
        suffix += 1

def generate_unique_examiner_id(existing_examiner_ids, counter):
    """Generate unique EMP-IND examiner id"""
    while True:
        candidate = f"EMP-IND-{counter:04d}"
        counter += 1
        if candidate not in existing_examiner_ids:
            existing_examiner_ids.add(candidate)
            return candidate, counter

def reset_existing_user_data(db):
    """Remove existing user rows and dependent records that reference users"""
    print("\n🧹 Resetting existing users and user-linked records...")

    # Remove team lead references first
    db.query(Team).update({Team.team_lead_id: None}, synchronize_session=False)
    db.flush()

    # Delete rows from all tables that reference users (except teams)
    dependent_tables = []
    for table in Base.metadata.sorted_tables:
        if table.name == "users":
            continue
        for fk in table.foreign_keys:
            if fk.column.table.name == "users":
                dependent_tables.append(table)
                break

    for table in reversed(dependent_tables):
        if table.name == "teams":
            continue
        db.execute(table.delete())

    deleted_users = db.query(User).delete(synchronize_session=False)
    db.commit()
    print(f"  ✅ Removed existing users: {deleted_users}")

def ensure_special_users(db, org_id, used_usernames, existing_examiner_ids, import_token_version):
    """Ensure required fixed users exist"""
    print("\n🔐 Ensuring required admin users...")

    special_users = [
        {
            "user_name": "prasanna",
            "password": "prasanna123",
            "user_role": "superadmin",
            "org_id": None,
            "examiner_id": "SYS-PRASANNA"
        },
        {
            "user_name": "sathish",
            "password": "sathish123",
            "user_role": "admin",
            "org_id": org_id,
            "examiner_id": "SYS-SATHISH"
        },
    ]

    for spec in special_users:
        username = spec["user_name"]
        used_usernames.add(username)

        examiner_id = spec["examiner_id"]
        if examiner_id in existing_examiner_ids:
            suffix = 2
            while f"{examiner_id}-{suffix}" in existing_examiner_ids:
                suffix += 1
            examiner_id = f"{examiner_id}-{suffix}"
        existing_examiner_ids.add(examiner_id)

        user = User(
            user_name=username,
            examiner_id=examiner_id,
            password_hash=get_password_hash(spec["password"]),
            user_role=spec["user_role"],
            org_id=spec["org_id"],
            is_active=True,
            token_version=import_token_version
        )
        db.add(user)
        print(f"  ✅ Added {username} ({spec['user_role']})")

    db.flush()

def create_teams(db, org_id):
    """Create teams from CSV file"""
    print("\n📋 Creating teams from CSV...")
    
    teams_map = {}
    csv_path = '/home/buddy/Work/ODS/Employee-performance-Tracker/ODS - Team Creation.csv'
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_name = row['Team Name'].strip()
            states_str = row['State'].strip()
            products_str = row['Product Type'].strip()
            
            # Parse states and products
            states = parse_comma_separated(states_str)
            products = parse_comma_separated(products_str)
            
            # Check if team already exists
            team = db.query(Team).filter(
                Team.name == team_name,
                Team.org_id == org_id
            ).first()
            
            if not team:
                # Create team
                team = Team(
                    name=team_name,
                    org_id=org_id,
                    daily_target=10,
                    monthly_target=200,
                    single_seat_score=1.0,
                    step1_score=0.5,
                    step2_score=0.5,
                    is_active=True
                )
                db.add(team)
                db.flush()
                
                # Add states
                for state in states:
                    team_state = TeamState(team_id=team.id, state=state)
                    db.add(team_state)
                
                # Add products
                for product in products:
                    team_product = TeamProduct(team_id=team.id, product_type=product)
                    db.add(team_product)
                
                print(f"  ✅ Created team: {team_name} ({len(states)} states, {len(products)} products)")
            else:
                print(f"  ℹ️  Team already exists: {team_name}")
            
            teams_map[team_name] = team
    
    db.commit()
    return teams_map

def create_users_and_assign_teams(db, org_id, teams_map, import_token_version):
    """Create users and assign them to teams from CSV file"""
    print("\n👥 Creating users and assigning to teams...")
    
    csv_path = '/home/buddy/Work/ODS/Employee-performance-Tracker/ODS - Team Members and Roles.csv'
    users_created = 0
    memberships_created = 0

    used_usernames = {row[0] for row in db.query(User.user_name).all()}
    existing_examiner_ids = {row[0] for row in db.query(User.examiner_id).all()}

    # Add fixed superadmin/admin accounts first so their usernames stay exact
    ensure_special_users(db, org_id, used_usernames, existing_examiner_ids, import_token_version)

    user_counter = 1
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            member_name = row['members'].strip()
            role = row['Role'].strip()
            team_name = row['Team Name'].strip()
            
            # Map role to system role (lowercase)
            if role.lower() == 'examiner':
                user_role = 'examiner'  # System role: examiner
            elif role.lower() == 'team lead':
                user_role = 'team_lead'  # System role: team_lead
            else:
                print(f"  ⚠️  Unknown role '{role}' for {member_name}, defaulting to examiner")
                user_role = 'examiner'
            
            # Create one user per CSV row (no dedupe by member name)
            base_username = normalize_username(member_name)
            username = generate_unique_username(base_username, used_usernames)
            examiner_id, user_counter = generate_unique_examiner_id(existing_examiner_ids, user_counter)

            user = User(
                user_name=username,
                examiner_id=examiner_id,
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                user_role=user_role,
                org_id=org_id,
                is_active=True,
                token_version=import_token_version
            )
            db.add(user)
            db.flush()
            users_created += 1
            
            # Get team
            team = teams_map.get(team_name)
            if not team:
                print(f"  ⚠️  Team '{team_name}' not found for user {member_name}")
                continue
            
            # Update team lead if role is Team Lead
            if user_role == 'team_lead' and not team.team_lead_id:
                team.team_lead_id = user.id
                db.flush()
            
            # Check if user is already in the team
            existing_membership = db.query(UserTeam).filter(
                UserTeam.user_id == user.id,
                UserTeam.team_id == team.id
            ).first()
            
            if not existing_membership:
                # Add user to team
                membership = UserTeam(
                    user_id=user.id,
                    team_id=team.id,
                    role='leader' if user_role == 'team_lead' else 'member',
                    is_active=True
                )
                db.add(membership)
                memberships_created += 1
    
    db.commit()
    print(f"  ✅ Created {users_created} users from CSV rows")
    print(f"  ✅ Added {memberships_created} user-team memberships")

def create_fa_names_and_assign(db, teams_map):
    """Create FA names and assign them to teams from CSV file"""
    print("\n📝 Creating FA names and assigning to teams...")
    
    csv_path = '/home/buddy/Work/ODS/Employee-performance-Tracker/ODS - Team FA Names.csv'
    fa_names_created = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # First row is team names
        team_names = next(reader)
        team_names = [name.strip() for name in team_names if name.strip()]
        
        # Rest of rows are FA names
        for row in reader:
            for idx, fa_name_str in enumerate(row):
                if idx >= len(team_names):
                    break
                
                fa_name_str = fa_name_str.strip()
                if not fa_name_str:
                    continue
                
                team_name = team_names[idx]
                
                # Get or create FA name
                fa_name = db.query(FAName).filter(FAName.name == fa_name_str).first()
                if not fa_name:
                    fa_name = FAName(name=fa_name_str, is_active=True)
                    db.add(fa_name)
                    db.flush()
                    fa_names_created += 1
                
                # Get team
                team = teams_map.get(team_name)
                if not team:
                    continue
                
                # Check if FA name is already assigned to this team
                existing_assignment = db.query(TeamFAName).filter(
                    TeamFAName.team_id == team.id,
                    TeamFAName.fa_name_id == fa_name.id
                ).first()
                
                if not existing_assignment:
                    team_fa_name = TeamFAName(
                        team_id=team.id,
                        fa_name_id=fa_name.id,
                        is_active=True
                    )
                    db.add(team_fa_name)
    
    db.commit()
    print(f"  ✅ Created/assigned {fa_names_created} FA names to teams")

def main():
    print("=" * 70)
    print("🚀 IMPORTING CSV DATA INTO DATABASE")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Get or create ODS India organization
        org = db.query(Organization).filter(Organization.code == "ORG-IND").first()
        if not org:
            print("\n⚠️  ODS India organization not found, creating it...")
            org = Organization(
                name="ODS - India",
                code="ORG-IND",
                is_active=True
            )
            db.add(org)
            db.commit()
            print("  ✅ Created organization: ODS - India")
        else:
            print(f"\n✅ Found organization: {org.name} (ID: {org.id})")
        
        # Step 1: Create teams
        teams_map = create_teams(db, org.id)

        # Step 2: Reset existing users and user-linked data
        reset_existing_user_data(db)

        # Use a fresh token version so old sessions become invalid after import
        import_token_version = int(datetime.utcnow().timestamp())
        
        # Step 3: Create users and assign to teams
        create_users_and_assign_teams(db, org.id, teams_map, import_token_version)
        
        # Step 4: Create FA names and assign to teams
        create_fa_names_and_assign(db, teams_map)
        
        # Print summary
        print("\n" + "=" * 70)
        print("✅ CSV DATA IMPORT COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        print("\n📊 SUMMARY:")
        print(f"  Organizations: {db.query(Organization).count()}")
        print(f"  Users: {db.query(User).count()}")
        print(f"  Teams: {db.query(Team).count()}")
        print(f"  Team States: {db.query(TeamState).count()}")
        print(f"  Team Products: {db.query(TeamProduct).count()}")
        print(f"  FA Names: {db.query(FAName).count()}")
        print(f"  Team FA Name Assignments: {db.query(TeamFAName).count()}")
        print(f"  User Team Memberships: {db.query(UserTeam).count()}")
        
        print("\n🔑 DEFAULT LOGIN CREDENTIALS:")
        print("  Password for all users: Test@123")
        print("\n  Sample Users:")
        # Show first 5 users
        users = db.query(User).limit(5).all()
        for user in users:
            print(f"  - {user.user_name} / Test@123 ({user.user_role})")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
