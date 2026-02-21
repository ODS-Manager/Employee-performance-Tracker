"""
Create Comprehensive Sample Orders
Generates orders for all teams with varied:
- Process types (Step1, Step2, Single Seat)
- Order statuses (Completed, On-hold, BP, RTI)
- Transaction types (Sale/Cash, Sale w/Mortgage, Refinance, HELOC, Other)
- Date range (last 60 days)
- All team states and product types
"""
import sqlite3
from datetime import datetime, timedelta, date
import random

# Connect to database
conn = sqlite3.connect('ods_db.sqlite')
cursor = conn.cursor()

# Get reference data
cursor.execute('SELECT id, name FROM process_types')
process_types = {row[1]: row[0] for row in cursor.fetchall()}

cursor.execute('SELECT id, name FROM order_status')
order_statuses = {row[1]: row[0] for row in cursor.fetchall()}

cursor.execute('SELECT id, name FROM transaction_types')
transaction_types = {row[1]: row[0] for row in cursor.fetchall()}

cursor.execute('SELECT id, name FROM divisions')
divisions = {row[1]: row[0] for row in cursor.fetchall()}

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
    
    teams_examiners[team_id] = {
        'name': team_name,
        'org_id': org_id,
        'states': states.split(',') if states else ['FL'],  # Default to FL if no states
        'products': products.split(',') if products else ['Full Search'],  # Default product
        'examiners': examiners
    }

print("=" * 100)
print("GENERATING SAMPLE ORDERS")
print("=" * 100)

# Date range: Last 60 days
end_date = date.today()
start_date = end_date - timedelta(days=60)

# Generate a range of dates
def get_random_date():
    """Generate random date within the last 60 days"""
    days_ago = random.randint(0, 60)
    return end_date - timedelta(days=days_ago)

def get_random_datetime(entry_date):
    """Generate random datetime for the given date"""
    hour = random.randint(8, 17)  # Business hours 8am-5pm
    minute = random.randint(0, 59)
    return datetime.combine(entry_date, datetime.min.time()).replace(hour=hour, minute=minute)

# Counties list for variety
counties = [
    'Miami-Dade', 'Orange', 'Hillsborough', 'Duval', 'Palm Beach',
    'Los Angeles', 'San Diego', 'San Francisco', 'Sacramento', 'Riverside',
    'Cook', 'DuPage', 'Lake', 'Will', 'Kane',
    'Harris', 'Dallas', 'Bexar', 'Travis', 'Tarrant',
    'King', 'Pierce', 'Snohomish', 'Clark', 'Thurston',
    'Maricopa', 'Pima', 'Pinal', 'Coconino', 'Yavapai'
]

# Billing statuses (must be 'pending' or 'done' per DB constraint)
billing_statuses = ['pending', 'done', None]

orders_created = 0
file_number_counter = 1000

print(f"\nGenerating orders for {len(teams_examiners)} teams from {start_date} to {end_date}")
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
    
    # Generate 20-50 orders per team for variety
    num_orders = random.randint(20, 50)
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
        examiner2 = random.choice(examiners)  # Can be same or different
        
        # Generate file number
        file_number = f"ORD-{state}-{file_number_counter:06d}"
        file_number_counter += 1
        
        # Determine which user fields to populate based on process type
        step1_user_id = None
        step1_start_time = None
        step1_end_time = None
        step2_user_id = None
        step2_start_time = None
        step2_end_time = None
        
        if process_type == 'Step1':
            # Only step1 fields populated
            step1_user_id = examiner1[0]
            step1_start = get_random_datetime(entry_date)
            step1_end = step1_start + timedelta(minutes=random.randint(30, 180))
            step1_start_time = step1_start.isoformat()
            step1_end_time = step1_end.isoformat()
            
        elif process_type == 'Step2':
            # Only step2 fields populated
            step2_user_id = examiner1[0]
            step2_start = get_random_datetime(entry_date)
            step2_end = step2_start + timedelta(minutes=random.randint(20, 120))
            step2_start_time = step2_start.isoformat()
            step2_end_time = step2_end.isoformat()
            
        elif process_type == 'Single Seat':
            # Both step1 and step2 fields populated (same or different user)
            step1_user_id = examiner1[0]
            step2_user_id = examiner2[0]  # Can be same as examiner1
            
            step1_start = get_random_datetime(entry_date)
            step1_end = step1_start + timedelta(minutes=random.randint(30, 180))
            step1_start_time = step1_start.isoformat()
            step1_end_time = step1_end.isoformat()
            
            # Step2 starts after step1
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
            billing_status, 2,  # Created by superadmin (user_id=2)
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        team_orders += 1
        orders_created += 1
    
    print(f"  Team {team_id:3} ({team_name:25}): {team_orders:3} orders created ({len(examiners)} examiners)")

# Commit all orders
conn.commit()

print("-" * 100)
print(f"\n✅ SUCCESS: Created {orders_created} sample orders across {len(teams_examiners)} teams")

# Show distribution summary
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
    print(f"  {row[0]:20}: {row[1]:5} orders")

cursor.execute("""
    SELECT 
        t.name,
        COUNT(*) as order_count,
        COUNT(DISTINCT o.step1_user_id) + COUNT(DISTINCT o.step2_user_id) as examiners_with_orders
    FROM orders o
    JOIN teams t ON o.team_id = t.id
    GROUP BY t.name
    ORDER BY order_count DESC
    LIMIT 10
""")
print("\nTop 10 Teams by Orders:")
for row in cursor.fetchall():
    print(f"  {row[0]:25}: {row[1]:5} orders, {row[2]:3} examiners active")

# Date range of orders
cursor.execute("""
    SELECT 
        MIN(entry_date) as earliest,
        MAX(entry_date) as latest,
        COUNT(DISTINCT entry_date) as unique_days
    FROM orders
""")
earliest, latest, unique_days = cursor.fetchone()
print(f"\nDate Range: {earliest} to {latest} ({unique_days} unique days)")

conn.close()

print("\n" + "=" * 100)
print("🎉 Sample orders generation complete!")
print("=" * 100)
