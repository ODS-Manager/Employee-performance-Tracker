#!/usr/bin/env python3
"""
Add missing team states and products data to existing teams
This script will populate team_states and team_products tables for existing teams
"""

import sys
import os

# Add the backend to Python path
sys.path.append('/home/buddy/Work/ODS/Employee-performance-Tracker/Backend')

# Set environment to use SQLite for now
os.environ['DATABASE_URL'] = 'sqlite:///./ods_development.db'

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.models.team import Team, TeamState, TeamProduct
    from app.models.organization import Organization
    from app.models.user import User
    from app.core.security import get_password_hash
    
    print("🚀 Adding missing team states and products data...")
    
    # Use SQLite for development
    engine = create_engine('sqlite:///./ods_development.db', echo=False)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Check if we have teams
    teams = session.query(Team).all()
    print(f"📊 Found {len(teams)} teams in database")
    
    if len(teams) == 0:
        print("⚠️  No teams found. Let me create some sample teams first...")
        
        # Create organizations if they don't exist
        org = session.query(Organization).first()
        if not org:
            org = Organization(name="ODS India", code="ODS-IND", is_active=True)
            session.add(org)
            session.commit()
            print("✅ Created organization")
        
        # Create a user for team lead if needed
        user = session.query(User).first() 
        if not user:
            user = User(
                user_name="admin",
                employee_id="EMP001",
                password_hash=get_password_hash("admin123"),
                user_role="ADMIN",
                org_id=org.id,
                is_active=True,
                token_version=1
            )
            session.add(user)
            session.commit()
            print("✅ Created user")
        
        # Create sample teams based on CSV data
        teams_data = [
            ("Florida", ["FL"], ["Full Search", "Update", "Date Down", "Amend Title", "Screening", "M&B"]),
            ("California", ["CA"], ["Full Search", "Update", "Date Down", "Amend Title"]),
            ("GI Clearing", ["AZ", "CA", "TX"], ["GI Clearing"]),
            ("Washington", ["WA"], ["Full Search", "Update", "Date Down", "Amend Title"]),
            ("Michigan", ["MI"], ["Full Search", "Update", "Date Down", "Amend Title"]),
        ]
        
        for team_name, states, products in teams_data:
            team = Team(
                name=team_name,
                org_id=org.id,
                team_lead_id=user.id,
                daily_target=10,
                monthly_target=200,
                single_seat_score=1.0,
                step1_score=0.5,
                step2_score=0.5,
                is_active=True
            )
            session.add(team)
            session.commit()
            
            # Add states
            for state in states:
                team_state = TeamState(team_id=team.id, state=state)
                session.add(team_state)
            
            # Add products
            for product in products:
                team_product = TeamProduct(team_id=team.id, product_type=product)
                session.add(team_product)
            
            print(f"✅ Created team: {team_name}")
        
        session.commit()
        teams = session.query(Team).all()
        print(f"✅ Created {len(teams)} teams with states and products")
    
    else:
        print("✅ Teams already exist. Checking if they have states and products...")
        
        # Check existing states and products
        existing_states = session.query(TeamState).count()
        existing_products = session.query(TeamProduct).count()
        
        print(f"📊 Existing team states: {existing_states}")
        print(f"📊 Existing team products: {existing_products}")
        
        if existing_states == 0 and existing_products == 0:
            print("🔧 Adding missing states and products to existing teams...")
            
            # Default mapping for teams without specific data
            default_states = ["CA", "FL", "TX", "NY", "AZ"]
            default_products = ["Full Search", "Update", "Date Down", "Amend Title"]
            
            for i, team in enumerate(teams):
                print(f"  📋 Adding data for team: {team.name}")
                
                # Add some states (cycle through defaults)
                states_to_add = default_states[i % len(default_states):i % len(default_states) + 2]
                for state in states_to_add:
                    # Check if state already exists
                    existing_state = session.query(TeamState).filter_by(team_id=team.id, state=state).first()
                    if not existing_state:
                        team_state = TeamState(team_id=team.id, state=state)
                        session.add(team_state)
                        print(f"    + State: {state}")
                
                # Add some products (cycle through defaults)
                products_to_add = default_products[i % len(default_products):i % len(default_products) + 2]
                for product in products_to_add:
                    # Check if product already exists
                    existing_product = session.query(TeamProduct).filter_by(team_id=team.id, product_type=product).first()
                    if not existing_product:
                        team_product = TeamProduct(team_id=team.id, product_type=product)
                        session.add(team_product)
                        print(f"    + Product: {product}")
            
            session.commit()
            print("✅ Added missing states and products!")
        else:
            print("ℹ️  Teams already have states and products data")
    
    # Final verification
    print("\n🔍 Final verification...")
    from sqlalchemy.orm import joinedload
    
    teams_with_data = session.query(Team).options(
        joinedload(Team.states),
        joinedload(Team.products)
    ).all()
    
    print(f"📊 Final counts:")
    print(f"  Teams: {len(teams_with_data)}")
    print(f"  Team States: {session.query(TeamState).count()}")
    print(f"  Team Products: {session.query(TeamProduct).count()}")
    
    print("\n📋 Teams with their data:")
    for team in teams_with_data:
        print(f"  🏗️  {team.name}")
        print(f"     States: {[s.state for s in team.states]}")
        print(f"     Products: {[p.product_type for p in team.products]}")
    
    # Test the API serialization
    print("\n🧪 Testing API serialization...")
    from app.api.v1.teams import serialize_team
    
    for team in teams_with_data[:2]:  # Test first 2 teams
        try:
            serialized = serialize_team(team)
            states_count = len(serialized.get('states', []))
            products_count = len(serialized.get('products', []))
            print(f"  ✅ {team.name}: {states_count} states, {products_count} products")
        except Exception as e:
            print(f"  ❌ {team.name}: Serialization error - {e}")
    
    session.close()
    print("\n🎉 Done! Your teams should now show states and products in the management page!")
    
except Exception as e:
    print(f"❌ Script failed: {e}")
    import traceback
    traceback.print_exc()