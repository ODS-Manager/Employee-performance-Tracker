#!/usr/bin/env python3
"""
Check existing database content to understand the current state
"""

import sys
import os

# Add the backend to Python path
sys.path.append('/home/buddy/Work/ODS/Employee-performance-Tracker/Backend')

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Try to use the actual database configuration
    try:
        from app.core.config import settings
        database_url = settings.DATABASE_URL
        print(f"📊 Using configured database: {database_url}")
    except:
        # Fallback to environment variable or default
        database_url = os.getenv('DATABASE_URL', 'postgresql://ods_user:ods_password@localhost:5432/ods_db')
        print(f"📊 Using fallback database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    print("✅ Connected to database successfully!")
    
    # Check what tables exist
    print("\n🔍 Checking existing tables...")
    tables_query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    try:
        result = session.execute(tables_query)
        tables = [row[0] for row in result.fetchall()]
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
    except Exception as e:
        print(f"⚠️  Could not list tables (might be SQLite): {e}")
        # For SQLite, try a different approach
        try:
            sqlite_tables = text("SELECT name FROM sqlite_master WHERE type='table';")
            result = session.execute(sqlite_tables)
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Found {len(tables)} SQLite tables:")
            for table in tables:
                print(f"  - {table}")
        except:
            print("❌ Could not determine table structure")
    
    # Check organizations
    print("\n🏢 Checking organizations...")
    orgs_query = text("SELECT id, name, code FROM organizations ORDER BY id;")
    try:
        result = session.execute(orgs_query)
        orgs = result.fetchall()
        print(f"📊 Found {len(orgs)} organizations:")
        for org in orgs:
            print(f"  - ID: {org[0]}, Name: {org[1]}, Code: {org[2]}")
    except Exception as e:
        print(f"❌ Error checking organizations: {e}")
    
    # Check users
    print("\n👥 Checking users...")
    users_query = text("SELECT id, user_name, user_role, org_id FROM users ORDER BY id LIMIT 10;")
    try:
        result = session.execute(users_query)
        users = result.fetchall()
        print(f"📊 Found {len(users)} users (showing first 10):")
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Role: {user[2]}, Org: {user[3]}")
    except Exception as e:
        print(f"❌ Error checking users: {e}")
    
    # Check teams
    print("\n🏗️  Checking teams...")
    teams_query = text("SELECT id, name, org_id, team_lead_id, is_active FROM teams ORDER BY id;")
    try:
        result = session.execute(teams_query)
        teams = result.fetchall()
        print(f"📊 Found {len(teams)} teams:")
        for team in teams:
            print(f"  - ID: {team[0]}, Name: {team[1]}, Org: {team[2]}, Lead: {team[3]}, Active: {team[4]}")
    except Exception as e:
        print(f"❌ Error checking teams: {e}")
        teams = []
    
    # Check team_states
    print("\n🗺️  Checking team_states...")
    try:
        states_query = text("SELECT team_id, state FROM team_states ORDER BY team_id, state;")
        result = session.execute(states_query)
        team_states = result.fetchall()
        print(f"📊 Found {len(team_states)} team state relationships:")
        
        # Group by team
        if team_states:
            current_team = None
            for team_id, state in team_states:
                if team_id != current_team:
                    print(f"  Team {team_id}:")
                    current_team = team_id
                print(f"    - {state}")
        else:
            print("❌ NO TEAM STATES FOUND - This is the issue!")
    except Exception as e:
        print(f"❌ Error checking team_states: {e}")
    
    # Check team_products  
    print("\n📦 Checking team_products...")
    try:
        products_query = text("SELECT team_id, product_type FROM team_products ORDER BY team_id, product_type;")
        result = session.execute(products_query)
        team_products = result.fetchall()
        print(f"📊 Found {len(team_products)} team product relationships:")
        
        # Group by team
        if team_products:
            current_team = None
            for team_id, product in team_products:
                if team_id != current_team:
                    print(f"  Team {team_id}:")
                    current_team = team_id
                print(f"    - {product}")
        else:
            print("❌ NO TEAM PRODUCTS FOUND - This is the issue!")
    except Exception as e:
        print(f"❌ Error checking team_products: {e}")
    
    # If we have teams but no states/products, this is our problem
    if len(teams) > 0:
        print(f"\n🔍 DIAGNOSIS:")
        print(f"✅ Teams exist: {len(teams)} teams found")
        try:
            states_count_query = text("SELECT COUNT(*) FROM team_states;")
            states_count = session.execute(states_count_query).fetchone()[0]
            products_count_query = text("SELECT COUNT(*) FROM team_products;") 
            products_count = session.execute(products_count_query).fetchone()[0]
            
            print(f"❌ Team states: {states_count} (should have data)")
            print(f"❌ Team products: {products_count} (should have data)")
            
            if states_count == 0 and products_count == 0:
                print("\n🚨 ROOT CAUSE IDENTIFIED:")
                print("   - Teams exist in database")
                print("   - BUT team_states and team_products tables are empty")
                print("   - This causes the API to return empty arrays for states/products")
                print("   - Need to populate team_states and team_products with actual data")
        except Exception as e:
            print(f"Could not get counts: {e}")
    
    session.close()
    print("\n✅ Database analysis complete!")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()