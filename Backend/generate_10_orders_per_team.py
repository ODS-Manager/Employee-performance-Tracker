#!/usr/bin/env python3
"""
Generate 10 orders per team (160 total) with all possible combinations
Covers all transaction types, statuses, process types, divisions
"""
import sqlite3
from datetime import datetime, timedelta
import random
import itertools

DB_PATH = "ods_db.sqlite"

# Reference data - EXACT VALUES
TRANSACTION_TYPES = [
    "Sale/Cash",
    "Sale w/Mortgage", 
    "Equity Loan",
    "Refinance",
    "Construction Loan",
    "Search Package",
    "Second Loan"
]

ORDER_STATUSES = [
    "Completed",
    "On-hold",
    "BP & RTI"
]

PROCESS_TYPES = [
    "Step1",
    "Step2",
    "Single Seat"
]

DIVISIONS = ["Direct", "Agency"]

# States (37 approved)
APPROVED_STATES = [
    "WA", "CA", "FL", "UT", "NV", "TX", "IL", "CO", "AZ", "HI",
    "IN", "MI", "PA", "GA", "MO", "OH", "OR", "SD", "ME", "KY",
    "NE", "OK", "KS", "WV", "CT", "NH", "AL", "SC", "NC", "DC",
    "IA", "VA", "TN", "MA", "WI", "ND", "RI"
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("GENERATING 10 ORDERS PER TEAM")
    print("=" * 80)
    
    # Step 1: Delete all existing orders
    print("\n[1/5] Deleting all existing orders...")
    cursor.execute("SELECT COUNT(*) FROM orders")
    old_count = cursor.fetchone()[0]
    print(f"  Found {old_count} existing orders")
    
    cursor.execute("DELETE FROM orders")
    conn.commit()
    print(f"  ✓ Deleted {old_count} orders")
    
    # Step 2: Get reference data IDs
    print("\n[2/5] Loading reference data...")
    
    # Transaction types
    cursor.execute("SELECT id, name FROM transaction_types ORDER BY id")
    transaction_type_map = {name: id for id, name in cursor.fetchall()}
    print(f"  Transaction types: {len(transaction_type_map)}")
    
    # Order statuses
    cursor.execute("SELECT id, name FROM order_status ORDER BY id")
    status_map = {name: id for id, name in cursor.fetchall()}
    print(f"  Order statuses: {len(status_map)}")
    
    # Process types
    cursor.execute("SELECT id, name FROM process_types ORDER BY id")
    process_type_map = {name: id for id, name in cursor.fetchall()}
    print(f"  Process types: {len(process_type_map)}")
    
    # Divisions
    cursor.execute("SELECT id, name FROM divisions ORDER BY id")
    division_map = {name: id for id, name in cursor.fetchall()}
    print(f"  Divisions: {len(division_map)}")
    
    # Step 3: Get teams and their data
    print("\n[3/5] Loading teams...")
    cursor.execute("""
        SELECT id, name, org_id 
        FROM teams 
        WHERE org_id = 3
        ORDER BY id
    """)
    teams = cursor.fetchall()
    print(f"  Found {len(teams)} teams")
    
    # Get team states
    team_states = {}
    for team_id, _, _ in teams:
        cursor.execute("""
            SELECT state 
            FROM team_states 
            WHERE team_id = ?
        """, (team_id,))
        states = [row[0] for row in cursor.fetchall()]
        # Filter to only approved states
        states = [s for s in states if s in APPROVED_STATES]
        team_states[team_id] = states if states else APPROVED_STATES[:5]  # fallback to 5 states
    
    # Get team products
    team_products = {}
    for team_id, _, _ in teams:
        cursor.execute("""
            SELECT product_type 
            FROM team_products 
            WHERE team_id = ?
        """, (team_id,))
        products = [row[0] for row in cursor.fetchall()]
        team_products[team_id] = products if products else ["Full search", "Update", "DateDown"]
    
    # Get team examiners
    team_examiners = {}
    for team_id, _, _ in teams:
        cursor.execute("""
            SELECT u.id, u.user_name 
            FROM users u
            JOIN user_teams ut ON u.id = ut.user_id
            WHERE ut.team_id = ? AND u.user_role = 'examiner' AND u.is_active = 1
        """, (team_id,))
        examiners = cursor.fetchall()
        team_examiners[team_id] = examiners if examiners else []
    
    # Step 4: Generate combinations
    print("\n[4/5] Generating order combinations...")
    
    # Create all possible combinations (7 trans × 3 status × 3 process × 2 div = 126 combinations)
    all_combinations = list(itertools.product(
        TRANSACTION_TYPES,
        ORDER_STATUSES,
        PROCESS_TYPES,
        DIVISIONS
    ))
    
    print(f"  Total possible combinations: {len(all_combinations)}")
    print(f"  Generating 10 orders per team...")
    
    # Step 5: Generate orders
    print("\n[5/5] Creating orders...")
    orders_created = 0
    start_date = datetime.now() - timedelta(days=60)
    
    for team_id, team_name, org_id in teams:
        print(f"\n  Team {team_id} ({team_name}):")
        
        # Select 10 random combinations (or cycle through if needed)
        selected_combinations = random.sample(all_combinations, min(10, len(all_combinations)))
        
        team_examiners_list = team_examiners[team_id]
        team_states_list = team_states[team_id]
        team_products_list = team_products[team_id]
        
        for idx, (trans_type, status, process_type, division) in enumerate(selected_combinations, 1):
            # Generate order details
            file_number = f"FILE-{team_id}-{datetime.now().strftime('%Y%m')}-{orders_created + 1:04d}"
            
            # Random dates within last 60 days
            days_ago = random.randint(0, 60)
            entry_date = start_date + timedelta(days=days_ago)
            
            # Select random examiner(s)
            step1_user_id = None
            step2_user_id = None
            
            if team_examiners_list:
                if process_type == "Step1":
                    step1_user_id = random.choice(team_examiners_list)[0]
                elif process_type == "Step2":
                    step2_user_id = random.choice(team_examiners_list)[0]
                elif process_type == "Single Seat":
                    # For Single Seat, use step1_user_id
                    step1_user_id = random.choice(team_examiners_list)[0]
            
            # Random state and product
            state = random.choice(team_states_list)
            product = random.choice(team_products_list)
            
            # Random county
            county = f"{state}-County-{random.randint(1, 10)}"
            
            # Default created_by to 1 (admin)
            created_by = 1
            
            # Create order
            cursor.execute("""
                INSERT INTO orders (
                    file_number, entry_date, team_id, org_id,
                    transaction_type_id, order_status_id, process_type_id, division_id,
                    state, county, product_type,
                    step1_user_id, step2_user_id,
                    billing_status, created_by, created_at, modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_number,
                entry_date.strftime('%Y-%m-%d'),
                team_id,
                org_id,
                transaction_type_map[trans_type],
                status_map[status],
                process_type_map[process_type],
                division_map[division],
                state,
                county,
                product,
                step1_user_id,
                step2_user_id,
                'pending' if status == 'Completed' else None,
                created_by,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            orders_created += 1
        
        print(f"    ✓ Created 10 orders (combinations: {', '.join([f'{t[:4]}+{s[:3]}+{p[:2]}+{d[0]}' for t,s,p,d in selected_combinations])})")
    
    conn.commit()
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    print(f"\nTotal orders created: {total_orders}")
    
    # Distribution by status
    print("\nBy Order Status:")
    cursor.execute("""
        SELECT os.name, COUNT(*) as count
        FROM orders o
        JOIN order_status os ON o.order_status_id = os.id
        GROUP BY os.name
        ORDER BY count DESC
    """)
    for status, count in cursor.fetchall():
        pct = (count / total_orders) * 100
        print(f"  {status:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Distribution by process type
    print("\nBy Process Type:")
    cursor.execute("""
        SELECT pt.name, COUNT(*) as count
        FROM orders o
        JOIN process_types pt ON o.process_type_id = pt.id
        GROUP BY pt.name
        ORDER BY count DESC
    """)
    for ptype, count in cursor.fetchall():
        pct = (count / total_orders) * 100
        print(f"  {ptype:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Distribution by transaction type
    print("\nBy Transaction Type:")
    cursor.execute("""
        SELECT tt.name, COUNT(*) as count
        FROM orders o
        JOIN transaction_types tt ON o.transaction_type_id = tt.id
        GROUP BY tt.name
        ORDER BY count DESC
    """)
    for ttype, count in cursor.fetchall():
        pct = (count / total_orders) * 100
        print(f"  {ttype:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Distribution by division
    print("\nBy Division:")
    cursor.execute("""
        SELECT d.name, COUNT(*) as count
        FROM orders o
        JOIN divisions d ON o.division_id = d.id
        GROUP BY d.name
        ORDER BY count DESC
    """)
    for div, count in cursor.fetchall():
        pct = (count / total_orders) * 100
        print(f"  {div:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Orders per team
    print("\nOrders per Team:")
    cursor.execute("""
        SELECT t.name, COUNT(*) as count
        FROM orders o
        JOIN teams t ON o.team_id = t.id
        GROUP BY t.name
        ORDER BY t.id
    """)
    for team, count in cursor.fetchall():
        print(f"  {team:30s}: {count:3d} orders")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ COMPLETED: Generated 10 orders per team with diverse combinations!")
    print("=" * 80)

if __name__ == "__main__":
    main()
