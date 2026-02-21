"""
Regenerate Sample Orders with Correct Reference Data
Deletes existing orders and creates new ones with correct:
- Transaction types (7)
- Process types (4 including "Step1 & Step2")
- Order statuses (4)
- Product types (23 - matching team assignments)
- States (37)
- Divisions (2)
"""
import sqlite3
from datetime import datetime, timedelta, date
import random

conn = sqlite3.connect('ods_db.sqlite')
cursor = conn.cursor()

print("=" * 100)
print("REGENERATING SAMPLE ORDERS WITH CORRECT REFERENCE DATA")
print("=" * 100)

# ============================================================================
# 1. DELETE EXISTING ORDERS
# ============================================================================
print("\n1. CLEANING UP EXISTING ORDERS...")
print("-" * 100)

cursor.execute('SELECT COUNT(*) FROM orders')
old_count = cursor.fetchone()[0]
print(f"   Found {old_count} existing orders")

cursor.execute('DELETE FROM orders')
print(f"   ✓ Deleted {old_count} orders")

# ============================================================================
# 2. GET REFERENCE DATA
# ============================================================================
print("\n2. LOADING REFERENCE DATA...")
print("-" * 100)

# Get reference data
cursor.execute('SELECT id, name FROM process_types')
process_types = {row[1]: row[0] for row in cursor.fetchall()}
print(f"   ✓ Process types: {len(process_types)}")

cursor.execute('SELECT id, name FROM order_status')
order_statuses = {row[1]: row[0] for row in cursor.fetchall()}
print(f"   ✓ Order statuses: {len(order_statuses)}")

cursor.execute('SELECT id, name FROM transaction_types')
transaction_types = {row[1]: row[0] for row in cursor.fetchall()}
print(f"   ✓ Transaction types: {len(transaction_types)}")

cursor.execute('SELECT id, name FROM divisions')
divisions = {row[1]: row[0] for row in cursor.fetchall()}
print(f"   ✓ Divisions: {len(divisions)}")

# Correct states list (37 states)
correct_states = ['WA','CA','FL','UT','NV','TX','IL','CO','AZ','HI','IN','MI','PA','GA','MO',
                  'OH','OR','SD','ME','KY','NE','OK','KS','WV','CT','NH','AL','SC','NC','DC',
                  'IA','VA','TN','MA','WI','ND','RI']
print(f"   ✓ States: {len(correct_states)}")

# ============================================================================
# 3. GET TEAMS DATA
# ============================================================================
print("\n3. LOADING TEAMS AND EXAMINERS...")
print("-" * 100)

# Get all teams with their states and products
cursor.execute("""
    SELECT 
        t.id,
        t.name,
        t.org_id,
        GROUP_CONCAT(DISTINCT ts.state) as states,
        GROUP_CONCAT(DISTINCT tp.product_type) as products
    FROM teams t
    LEFT JOIN team_states ts ON t.id = ts.team_id
    LEFT JOIN team_products tp ON t.id = tp.team_id
    GROUP BY t.id, t.name, t.org_id
    ORDER BY t.id
""")
teams_data = cursor.fetchall()

# Get examiners per team
teams_examiners = {}
for team_id, team_name, org_id, states, products in teams_data:
    cursor.execute("""
        SELECT u.id, u.user_name, u.examiner_id
        FROM users u
        JOIN user_teams ut ON u.id = ut.user_id
        WHERE ut.team_id = ? AND u.user_role = 'examiner' AND ut.is_active = 1
    """, (team_id,))
    examiners = cursor.fetchall()
    
    # Parse states and products
    team_states = states.split(',') if states else []
    team_products = products.split(',') if products else []
    
    # Filter states to only include approved ones
    approved_team_states = [s for s in team_states if s in correct_states]
    if not approved_team_states:
        approved_team_states = [random.choice(correct_states)]
    
    teams_examiners[team_id] = {
        'name': team_name,
        'org_id': org_id,
        'states': approved_team_states,
        'products': team_products if team_products else ['Full Search'],
        'examiners': examiners
    }

print(f"   ✓ Loaded {len(teams_examiners)} teams")

# ============================================================================
# 4. GENERATE ORDERS
# ============================================================================
print("\n4. GENERATING NEW ORDERS...")
print("-" * 100)

# Date range: Last 60 days
end_date = date.today()
start_date = end_date - timedelta(days=60)

def get_random_date():
    """Generate random date within the last 60 days"""
    days_ago = random.randint(0, 60)
    return end_date - timedelta(days=days_ago)

def get_random_datetime(entry_date):
    """Generate random datetime for the given date"""
    hour = random.randint(8, 17)
    minute = random.randint(0, 59)
    return datetime.combine(entry_date, datetime.min.time()).replace(hour=hour, minute=minute)

# Counties for variety
counties = [
    'Miami-Dade', 'Orange', 'Hillsborough', 'Duval', 'Palm Beach',
    'Los Angeles', 'San Diego', 'San Francisco', 'Sacramento', 'Riverside',
    'Cook', 'DuPage', 'Lake', 'Will', 'Kane',
    'Harris', 'Dallas', 'Bexar', 'Travis', 'Tarrant',
    'King', 'Pierce', 'Snohomish', 'Clark', 'Thurston',
    'Maricopa', 'Pima', 'Pinal', 'Coconino', 'Yavapai',
    'Wayne', 'Oakland', 'Macomb', 'Kent', 'Genesee',
    'Franklin', 'Cuyahoga', 'Hamilton', 'Summit', 'Montgomery'
]

billing_statuses = ['pending', 'done', None]

orders_created = 0
file_number_counter = 2000

print(f"Generating orders for {len(teams_examiners)} teams from {start_date} to {end_date}")
print("-" * 100)

for team_id, team_info in teams_examiners.items():
    team_name = team_info['name']
    org_id = team_info['org_id']
    states = team_info['states']
    products = team_info['products']
    examiners = team_info['examiners']
    
    if not examiners:
        print(f"  Team {team_id:3} ({team_name:25}): No examiners - SKIPPED")
        continue
    
    # Generate 30-60 orders per team
    num_orders = random.randint(30, 60)
    team_orders = 0
    
    for _ in range(num_orders):
        # Random selections
        entry_date = get_random_date()
        state = random.choice(states)
        county = random.choice(counties)
        product_type = random.choice(products)
        transaction_type = random.choice(list(transaction_types.keys()))
        process_type = random.choice(list(process_types.keys()))
        order_status = random.choice(list(order_statuses.keys()))
        division = random.choice(list(divisions.keys()))
        billing_status = random.choice(billing_statuses)
        
        # Random examiner(s) from team
        examiner1 = random.choice(examiners)
        examiner2 = random.choice(examiners)
        
        # Generate file number
        file_number = f"ORD-{state}-{file_number_counter:06d}"
        file_number_counter += 1
        
        # Populate user fields based on process type
        step1_user_id = None
        step1_start_time = None
        step1_end_time = None
        step2_user_id = None
        step2_start_time = None
        step2_end_time = None
        
        if process_type == 'Step1':
            step1_user_id = examiner1[0]
            step1_start = get_random_datetime(entry_date)
            step1_end = step1_start + timedelta(minutes=random.randint(30, 180))
            step1_start_time = step1_start.isoformat()
            step1_end_time = step1_end.isoformat()
            
        elif process_type == 'Step2':
            step2_user_id = examiner1[0]
            step2_start = get_random_datetime(entry_date)
            step2_end = step2_start + timedelta(minutes=random.randint(20, 120))
            step2_start_time = step2_start.isoformat()
            step2_end_time = step2_end.isoformat()
            
        elif process_type in ['Single Seat', 'Step1 & Step2']:
            # Both steps
            step1_user_id = examiner1[0]
            step2_user_id = examiner2[0]
            
            step1_start = get_random_datetime(entry_date)
            step1_end = step1_start + timedelta(minutes=random.randint(30, 180))
            step1_start_time = step1_start.isoformat()
            step1_end_time = step1_end.isoformat()
            
            step2_start = step1_end + timedelta(minutes=random.randint(10, 60))
            step2_end = step2_start + timedelta(minutes=random.randint(20, 120))
            step2_start_time = step2_start.isoformat()
            step2_end_time = step2_end.isoformat()
        
        # Insert order
        cursor.execute("""
            INSERT INTO orders (
                file_number, entry_date, transaction_type_id, process_type_id,
                order_status_id, division_id, state, county, product_type,
                team_id, org_id,
                step1_user_id, step1_start_time, step1_end_time,
                step2_user_id, step2_start_time, step2_end_time,
                billing_status, created_by, created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_number, entry_date.isoformat(),
            transaction_types[transaction_type], process_types[process_type],
            order_statuses[order_status], divisions[division],
            state, county, product_type, team_id, org_id,
            step1_user_id, step1_start_time, step1_end_time,
            step2_user_id, step2_start_time, step2_end_time,
            billing_status, 2,
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        team_orders += 1
        orders_created += 1
    
    print(f"  Team {team_id:3} ({team_name:25}): {team_orders:3} orders ({len(examiners)} examiners)")

conn.commit()

print("-" * 100)
print(f"\n✅ SUCCESS: Created {orders_created} new orders")

# ============================================================================
# 5. VERIFICATION
# ============================================================================
print("\n" + "=" * 100)
print("ORDER DISTRIBUTION SUMMARY")
print("=" * 100)

cursor.execute("""
    SELECT pt.name, COUNT(*) as count
    FROM orders o
    JOIN process_types pt ON o.process_type_id = pt.id
    GROUP BY pt.name
    ORDER BY count DESC
""")
print("\nBy Process Type:")
for row in cursor.fetchall():
    print(f"  {row[0]:20}: {row[1]:5} orders")

cursor.execute("""
    SELECT os.name, COUNT(*) as count
    FROM orders o
    JOIN order_status os ON o.order_status_id = os.id
    GROUP BY os.name
    ORDER BY count DESC
""")
print("\nBy Status:")
for row in cursor.fetchall():
    print(f"  {row[0]:20}: {row[1]:5} orders")

cursor.execute("""
    SELECT tt.name, COUNT(*) as count
    FROM orders o
    JOIN transaction_types tt ON o.transaction_type_id = tt.id
    GROUP BY tt.name
    ORDER BY count DESC
""")
print("\nBy Transaction Type:")
for row in cursor.fetchall():
    print(f"  {row[0]:30}: {row[1]:5} orders")

cursor.execute("""
    SELECT 
        t.name,
        COUNT(*) as order_count
    FROM orders o
    JOIN teams t ON o.team_id = t.id
    GROUP BY t.name
    ORDER BY order_count DESC
""")
print("\nTop Teams by Orders:")
for row in cursor.fetchall():
    print(f"  {row[0]:25}: {row[1]:5} orders")

cursor.execute("""
    SELECT 
        MIN(entry_date) as earliest,
        MAX(entry_date) as latest,
        COUNT(DISTINCT entry_date) as unique_days,
        COUNT(DISTINCT state) as unique_states,
        COUNT(DISTINCT product_type) as unique_products
    FROM orders
""")
earliest, latest, unique_days, unique_states, unique_products = cursor.fetchone()
print(f"\nMiscellaneous:")
print(f"  Date Range: {earliest} to {latest} ({unique_days} unique days)")
print(f"  Unique States: {unique_states}")
print(f"  Unique Products: {unique_products}")

conn.close()

print("\n" + "=" * 100)
print("🎉 ORDERS REGENERATION COMPLETE!")
print("=" * 100)
