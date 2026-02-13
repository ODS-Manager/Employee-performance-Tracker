#!/usr/bin/env python3
"""
Database connectivity test to verify actual data in the database
"""

import sys
import os

# Add the backend to Python path
sys.path.append('/home/buddy/Work/ODS/Employee-performance-Tracker/Backend')

# Set environment variables for database connection
os.environ['DATABASE_URL'] = 'sqlite:///./test_db.sqlite'  # Use SQLite for testing
os.environ['SECRET_KEY'] = 'test-secret-key-for-debugging'

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.models.team import Team, TeamState, TeamProduct
    from app.database import Base
    
    # Create SQLite database for testing
    engine = create_engine('sqlite:///./test_db.sqlite', echo=True)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    print("✅ Database connection successful!")
    
    # Test 1: Check if teams table has data
    teams_count = session.query(Team).count()
    print(f"📊 Teams in database: {teams_count}")
    
    # Test 2: Check if team_states has data  
    states_count = session.query(TeamState).count()
    print(f"📊 Team states in database: {states_count}")
    
    # Test 3: Check if team_products has data
    products_count = session.query(TeamProduct).count() 
    print(f"📊 Team products in database: {products_count}")
    
    if teams_count == 0:
        print("⚠️  No teams found - database may not be populated")
        
        # Try to add some test data
        print("🔧 Adding test data...")
        
        # Add a test organization first (if needed)
        from app.models.organization import Organization
        org = Organization(name="Test Organization")
        session.add(org)
        session.commit()
        
        # Add a test team
        team = Team(name="Test Team", org_id=org.id, daily_target=10)
        session.add(team)
        session.commit()
        
        # Add test states
        state1 = TeamState(team_id=team.id, state="CA")
        state2 = TeamState(team_id=team.id, state="FL")
        session.add_all([state1, state2])
        
        # Add test products
        product1 = TeamProduct(team_id=team.id, product_type="Full Search")
        product2 = TeamProduct(team_id=team.id, product_type="Update")
        session.add_all([product1, product2])
        
        session.commit()
        print("✅ Test data added successfully")
    
    # Test 4: Try the actual query with joinedload (like the API does)
    from sqlalchemy.orm import joinedload
    from app.api.v1.teams import serialize_team
    
    print("\n🔍 Testing team query with relationships...")
    
    teams_with_relations = session.query(Team).options(
        joinedload(Team.states),
        joinedload(Team.products)
    ).all()
    
    for team in teams_with_relations:
        print(f"\n📋 Team: {team.name}")
        print(f"  States: {[s.state for s in team.states]}")
        print(f"  Products: {[p.product_type for p in team.products]}")
        
        # Test serialization
        try:
            serialized = serialize_team(team)
            print(f"  Serialized states: {len(serialized.get('states', []))}")
            print(f"  Serialized products: {len(serialized.get('products', []))}")
            print(f"  Sample serialized: {serialized}")
        except Exception as e:
            print(f"  ❌ Serialization error: {e}")
    
    session.close()
    print("\n✅ Database test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the Backend directory and dependencies are installed")
except Exception as e:
    print(f"❌ Database test failed: {e}")
    import traceback
    traceback.print_exc()