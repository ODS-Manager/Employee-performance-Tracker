#!/usr/bin/env python3
"""
Generate SQL to populate missing team states and products based on existing teams
This script will help fix the empty display issue in team management
"""

# Sample team data structure - update this based on actual teams in production
# This is based on what we saw in the API responses
TEAMS_DATA = [
    {
        "id": 13,
        "name": "Arizona",
        "states": ["AZ"],
        "products": ["Full Search", "Update", "Date Down", "Amend Title"]
    },
    # Add more teams as needed
]

def generate_team_data_sql():
    """Generate SQL statements to populate team_states and team_products"""
    
    print("-- SQL to populate missing team_states and team_products")
    print("-- Generated for Employee Performance Tracker")
    print("-- Run this against your PostgreSQL database")
    print()
    
    # Generate team_states inserts
    print("-- Insert team states")
    print("INSERT INTO team_states (team_id, state, created_at, modified_at) VALUES")
    
    state_values = []
    for team in TEAMS_DATA:
        for state in team["states"]:
            state_values.append(f"({team['id']}, '{state}', NOW(), NOW())")
    
    if state_values:
        print(",\n".join(state_values))
        print("ON CONFLICT (team_id, state) DO NOTHING;")
    else:
        print("-- No states to insert")
    
    print()
    
    # Generate team_products inserts
    print("-- Insert team products")
    print("INSERT INTO team_products (team_id, product_type, created_at, modified_at) VALUES")
    
    product_values = []
    for team in TEAMS_DATA:
        for product in team["products"]:
            product_values.append(f"({team['id']}, '{product}', NOW(), NOW())")
    
    if product_values:
        print(",\n".join(product_values))
        print("ON CONFLICT (team_id, product_type) DO NOTHING;")
    else:
        print("-- No products to insert")
    
    print()
    
    # Generate verification query
    print("-- Verify the data was inserted")
    print("""
SELECT 
    t.id,
    t.name,
    COUNT(DISTINCT ts.state) as state_count,
    COUNT(DISTINCT tp.product_type) as product_count,
    STRING_AGG(DISTINCT ts.state, ', ') as states,
    STRING_AGG(DISTINCT tp.product_type, ', ') as products
FROM teams t
LEFT JOIN team_states ts ON t.id = ts.team_id  
LEFT JOIN team_products tp ON t.id = tp.team_id
GROUP BY t.id, t.name
ORDER BY t.id;
""")

def generate_comprehensive_team_data():
    """Generate comprehensive team data for typical insurance company structure"""
    
    # Common states for insurance teams
    common_states = [
        ["FL", "GA"], ["CA", "NV"], ["TX", "OK"], ["NY", "NJ"], 
        ["AZ", "NM"], ["WA", "OR"], ["MI", "OH"], ["NC", "SC"],
        ["IL", "IN"], ["PA", "MD"]
    ]
    
    # Common product types
    common_products = [
        ["Full Search", "Update", "Date Down", "Amend Title"],
        ["GI Clearing", "Full Search", "Screening"],
        ["Full Search", "Update", "Vendor Exam", "M&B"],
        ["Screening", "M&B", "Clearance", "Full Search"],
        ["Full Search", "Update", "Date Down", "Amend Title", "Screening"]
    ]
    
    print("\n-- Comprehensive team data for teams 1-20 (adjust IDs as needed)")
    
    # Generate for team IDs 1-20 with various combinations
    teams = []
    for i in range(1, 21):
        state_idx = (i - 1) % len(common_states)
        product_idx = (i - 1) % len(common_products)
        
        teams.append({
            "id": i,
            "name": f"Team_{i:02d}",
            "states": common_states[state_idx],
            "products": common_products[product_idx]
        })
    
    # Update TEAMS_DATA globally
    global TEAMS_DATA
    TEAMS_DATA = teams
    
    generate_team_data_sql()

if __name__ == "__main__":
    print("Choose option:")
    print("1. Generate SQL for specific Arizona team (ID 13)")
    print("2. Generate comprehensive SQL for teams 1-20")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        generate_team_data_sql()
    elif choice == "2":
        generate_comprehensive_team_data()
    else:
        print("Invalid choice. Generating for Arizona team by default.")
        generate_team_data_sql()