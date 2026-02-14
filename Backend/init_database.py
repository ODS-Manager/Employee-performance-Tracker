#!/usr/bin/env python3
"""
Database initialization script for Employee Performance Tracker
This script will set up the database with all required tables and data.
"""

import sys
import os

# Add the backend to Python path
sys.path.append('/home/buddy/Work/ODS/Employee-performance-Tracker/Backend')

# Import required modules
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.models import *  # Import all models
    from app.core.security import get_password_hash
    import csv
    from datetime import datetime
    
    print("🚀 Starting database initialization...")
    
    # Get database URL from environment or use SQLite for local testing
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("⚠️  No DATABASE_URL found, using SQLite for testing")
        db_url = 'sqlite:///./ods_db.sqlite'
    
    print(f"📊 Connecting to database: {db_url}")
    
    # Create engine and session
    engine = create_engine(db_url, echo=False)  # Set to True for SQL debugging
    
    # Create all tables
    print("🏗️  Creating database tables...")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    print("✅ Database tables created successfully!")
    
    # Check if data already exists
    from app.models.organization import Organization
    from app.models.team import Team, TeamState, TeamProduct
    from app.models.user import User
    
    existing_orgs = session.query(Organization).count()
    if existing_orgs > 0:
        print("ℹ️  Database already has data. Skipping initialization.")
        print(f"   Organizations: {session.query(Organization).count()}")
        print(f"   Teams: {session.query(Team).count()}")
        print(f"   Team States: {session.query(TeamState).count()}")
        print(f"   Team Products: {session.query(TeamProduct).count()}")
        session.close()
        sys.exit(0)
    
    print("📝 Initializing database with sample data...")
    
    # 1. Create Organizations
    print("  🏢 Creating organizations...")
    org_ods_ind = Organization(name="ODS India", code="ODS-IND", is_active=True)
    org_ods_vnm = Organization(name="ODS Vietnam", code="ODS-VNM", is_active=True)
    session.add_all([org_ods_ind, org_ods_vnm])
    session.commit()
    
    # 2. Create Users with proper authentication
    print("  👥 Creating users...")
    users_data = [
        ("admin", "admin123", "ADMIN", org_ods_ind.id, "EMP001"),
        ("superadmin", "superadmin123", "SUPERADMIN", org_ods_ind.id, "EMP000"),
        ("teamlead", "admin123", "TEAM_LEAD", org_ods_ind.id, "EMP002"),
        ("employee", "admin123", "EMPLOYEE", org_ods_ind.id, "EMP003"),
    ]
    
    for username, password, role, org_id, emp_id in users_data:
        user = User(
            user_name=username,
            employee_id=emp_id,
            password_hash=get_password_hash(password),
            user_role=role,
            org_id=org_id,
            is_active=True,
            token_version=1
        )
        session.add(user)
    session.commit()
    
    # 3. Create Teams from CSV data
    print("  🏗️  Creating teams from CSV data...")
    
    # Parse the CSV data (simplified version of what's in our SQL script)
    teams_data = [
        ("Florida", "FL", ["Full Search", "Update", "Date Down", "Amend Title", "Screening", "M&B"]),
        ("California", "CA", ["Full Search", "Update", "Date Down", "Amend Title"]),
        ("GI Clearing", ["AZ", "CA", "TX"], ["GI Clearing"]),
        ("Washington", "WA", ["Full Search", "Update", "Date Down", "Amend Title"]),
        ("Michigan", "MI", ["Full Search", "Update", "Date Down", "Amend Title"]),
        ("Colorado", "CO", ["Full Search", "Update", "Date Down", "Amend Title"]),
        ("Utah", "UT", ["Full Search", "Update", "Date Down", "Amend Title"]),
        ("Oregon", "OR", ["Full Search", "Update", "Date Down", "Amend Title"]),
    ]
    
    for team_data in teams_data:
        team_name = team_data[0]
        states = team_data[1] if isinstance(team_data[1], list) else [team_data[1]]
        products = team_data[2]
        
        # Create team
        team = Team(
            name=team_name,
            org_id=org_ods_ind.id,
            daily_target=10,
            monthly_target=200,
            single_seat_score=1.0,
            step1_score=0.5,
            step2_score=0.5,
            is_active=True
        )
        session.add(team)
        session.commit()  # Commit to get the team ID
        
        # Add states
        for state in states:
            team_state = TeamState(team_id=team.id, state=state)
            session.add(team_state)
        
        # Add products
        for product in products:
            team_product = TeamProduct(team_id=team.id, product_type=product)
            session.add(team_product)
    
    session.commit()
    
    # 4. Add some FA Names
    print("  📝 Creating FA names...")
    from app.models.fa_name import FAName
    from app.models.team_fa_name import TeamFAName
    
    fa_names = ["Aaron", "Adam", "Alan", "Albert", "Alex", "Alisa", "Ally", "Amelia", "Anding", "Angelina"]
    fa_name_objects = []
    for name in fa_names:
        fa_name = FAName(name=name, is_active=True)
        session.add(fa_name)
        fa_name_objects.append(fa_name)
    
    session.commit()
    
    # Link some FA names to teams
    teams = session.query(Team).all()
    for i, team in enumerate(teams[:5]):  # Link to first 5 teams
        for j in range(2):  # 2 FA names per team
            if i * 2 + j < len(fa_name_objects):
                team_fa_name = TeamFAName(
                    team_id=team.id,
                    fa_name_id=fa_name_objects[i * 2 + j].id,
                    is_active=True
                )
                session.add(team_fa_name)
    
    session.commit()
    
    # Print summary
    print("\n🎉 Database initialization completed successfully!")
    print("\n📊 Summary:")
    print(f"  Organizations: {session.query(Organization).count()}")
    print(f"  Users: {session.query(User).count()}")
    print(f"  Teams: {session.query(Team).count()}")
    print(f"  Team States: {session.query(TeamState).count()}")
    print(f"  Team Products: {session.query(TeamProduct).count()}")
    print(f"  FA Names: {session.query(FAName).count()}")
    
    # Test the team query with relationships
    print("\n🔍 Testing team relationships...")
    from sqlalchemy.orm import joinedload
    
    teams_with_relations = session.query(Team).options(
        joinedload(Team.states),
        joinedload(Team.products),
        joinedload(Team.fa_names)
    ).all()
    
    for team in teams_with_relations[:3]:  # Show first 3 teams
        print(f"  📋 Team: {team.name}")
        print(f"     States: {[s.state for s in team.states]}")
        print(f"     Products: {[p.product_type for p in team.products]}")
        print(f"     FA Names: {len(team.fa_names)}")
    
    print("\n🔐 Test credentials created:")
    print("  - admin / admin123 (Admin)")
    print("  - superadmin / superadmin123 (Superadmin)")
    print("  - teamlead / admin123 (Team Lead)")
    print("  - employee / admin123 (Employee)")
    
    session.close()
    print("\n✅ Database is ready for use!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're in the Backend directory and dependencies are installed")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)