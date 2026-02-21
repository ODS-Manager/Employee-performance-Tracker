"""
Fix Reference Data - Update to Correct Values
Updates all reference tables and existing orders to match correct pre-seeded data
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('ods_db.sqlite')
cursor = conn.cursor()

print("=" * 100)
print("FIXING REFERENCE DATA")
print("=" * 100)

# ============================================================================
# 1. FIX TRANSACTION TYPES
# ============================================================================
print("\n1. FIXING TRANSACTION TYPES...")
print("-" * 100)

# Correct transaction types
correct_transaction_types = [
    'Sale/Cash',
    'Sale w/Mortgage', 
    'Equity Loan',
    'Refinance',
    'Construction Loan',
    'Search Package',
    'Second Loan'
]

# Clear existing transaction types
cursor.execute('DELETE FROM transaction_types')

# Insert correct transaction types
for i, name in enumerate(correct_transaction_types, 1):
    cursor.execute("""
        INSERT INTO transaction_types (id, name, created_at, modified_at)
        VALUES (?, ?, ?, ?)
    """, (i, name, datetime.now().isoformat(), datetime.now().isoformat()))
    print(f"   ✓ {i}: {name}")

print(f"   Total: {len(correct_transaction_types)} transaction types")

# ============================================================================
# 2. VERIFY ORDER STATUSES (already correct)
# ============================================================================
print("\n2. VERIFYING ORDER STATUSES...")
print("-" * 100)

cursor.execute('SELECT id, name FROM order_status ORDER BY id')
statuses = cursor.fetchall()
for s in statuses:
    print(f"   ✓ {s[0]}: {s[1]}")

# ============================================================================
# 3. FIX PROCESS TYPES (add "Step1 & Step2")
# ============================================================================
print("\n3. FIXING PROCESS TYPES...")
print("-" * 100)

# Check if "Step1 & Step2" exists
cursor.execute("SELECT id, name FROM process_types WHERE name = 'Step1 & Step2'")
step_both = cursor.fetchone()

if not step_both:
    # Add "Step1 & Step2" as id=4
    cursor.execute("""
        INSERT INTO process_types (id, name, created_at, modified_at)
        VALUES (4, 'Step1 & Step2', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    print("   ✓ Added: 4: Step1 & Step2")
else:
    print("   ✓ Already exists: 4: Step1 & Step2")

cursor.execute('SELECT id, name FROM process_types ORDER BY id')
for row in cursor.fetchall():
    print(f"   ✓ {row[0]}: {row[1]}")

# ============================================================================
# 4. VERIFY DIVISIONS (already correct)
# ============================================================================
print("\n4. VERIFYING DIVISIONS...")
print("-" * 100)

cursor.execute('SELECT id, name FROM divisions ORDER BY id')
divisions = cursor.fetchall()
for d in divisions:
    print(f"   ✓ {d[0]}: {d[1]}")

# ============================================================================
# 5. UPDATE EXISTING ORDERS WITH CORRECT DATA
# ============================================================================
print("\n5. UPDATING EXISTING ORDERS...")
print("-" * 100)

# Get all orders
cursor.execute('SELECT COUNT(*) FROM orders')
order_count = cursor.fetchone()[0]
print(f"   Found {order_count} orders to update")

# Update orders to use correct transaction types (map old to new)
# Old: 1=Sale/Cash, 2=Sale w/Mortgage, 3=Refinance, 4=HELOC, 5=Other
# New: 1=Sale/Cash, 2=Sale w/Mortgage, 3=Equity Loan, 4=Refinance, 5=Construction Loan, 6=Search Package, 7=Second Loan

import random

cursor.execute('SELECT id, transaction_type_id FROM orders')
orders = cursor.fetchall()

for order_id, old_trans_id in orders:
    # Map old transaction types to new ones
    if old_trans_id == 1:  # Sale/Cash -> Sale/Cash
        new_trans_id = 1
    elif old_trans_id == 2:  # Sale w/Mortgage -> Sale w/Mortgage
        new_trans_id = 2
    elif old_trans_id == 3:  # Refinance -> Refinance
        new_trans_id = 4
    elif old_trans_id == 4:  # HELOC -> Equity Loan
        new_trans_id = 3
    elif old_trans_id == 5:  # Other -> Random from new types
        new_trans_id = random.choice([5, 6, 7])  # Construction Loan, Search Package, Second Loan
    else:
        new_trans_id = random.choice(range(1, 8))
    
    cursor.execute('UPDATE orders SET transaction_type_id = ? WHERE id = ?', (new_trans_id, order_id))

print(f"   ✓ Updated transaction_type_id for {len(orders)} orders")

# Update product types in orders to match team_products
# Fix common mismatches
cursor.execute("""
    UPDATE orders 
    SET product_type = 'Full Search' 
    WHERE product_type LIKE 'Full search%' OR product_type = 'Full search'
""")

cursor.execute("""
    UPDATE orders 
    SET product_type = 'Date Down' 
    WHERE product_type = 'DateDown'
""")

print("   ✓ Fixed product type capitalization")

# Ensure states are in the correct 37-state list
correct_states = ['WA','CA','FL','UT','NV','TX','IL','CO','AZ','HI','IN','MI','PA','GA','MO',
                  'OH','OR','SD','ME','KY','NE','OK','KS','WV','CT','NH','AL','SC','NC','DC',
                  'IA','VA','TN','MA','WI','ND','RI']

# Update orders with states not in the list
cursor.execute('SELECT DISTINCT state FROM orders')
order_states = [row[0] for row in cursor.fetchall()]

for state in order_states:
    if state not in correct_states:
        # Map to nearest state or random from correct list
        if state.startswith('DE'):
            new_state = 'PA'  # Delaware -> Pennsylvania
        elif state in ['GA-ATO', 'MA-ATO', 'NC-ATO', 'RI-ATO', 'SC-ATO']:
            new_state = state.split('-')[0]  # Remove -ATO suffix
        elif state in ['MD', 'NJ', 'NM', 'MN', 'MS', 'MT', 'VT']:
            # States not in the approved list - pick nearby state
            new_state = random.choice(['PA', 'VA', 'NC', 'TN', 'KY'])
        else:
            new_state = random.choice(correct_states)
        
        cursor.execute('UPDATE orders SET state = ? WHERE state = ?', (new_state, state))
        print(f"   ✓ Mapped state {state} -> {new_state}")

print("   ✓ Fixed order states to match approved list")

# ============================================================================
# 6. COMMIT CHANGES
# ============================================================================
conn.commit()

print("\n" + "=" * 100)
print("VERIFICATION - UPDATED REFERENCE DATA")
print("=" * 100)

print("\nTransaction Types:")
cursor.execute('SELECT id, name FROM transaction_types ORDER BY id')
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}")

print("\nProcess Types:")
cursor.execute('SELECT id, name FROM process_types ORDER BY id')
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}")

print("\nOrder Statuses:")
cursor.execute('SELECT id, name FROM order_status ORDER BY id')
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}")

print("\nOrder Statistics:")
cursor.execute("""
    SELECT 
        tt.name,
        COUNT(*) as count
    FROM orders o
    JOIN transaction_types tt ON o.transaction_type_id = tt.id
    GROUP BY tt.name
    ORDER BY count DESC
""")
print("  By Transaction Type:")
for row in cursor.fetchall():
    print(f"    {row[0]:30}: {row[1]:4} orders")

cursor.execute("""
    SELECT 
        pt.name,
        COUNT(*) as count
    FROM orders o
    JOIN process_types pt ON o.process_type_id = pt.id
    GROUP BY pt.name
    ORDER BY count DESC
""")
print("\n  By Process Type:")
for row in cursor.fetchall():
    print(f"    {row[0]:30}: {row[1]:4} orders")

cursor.execute("""
    SELECT 
        os.name,
        COUNT(*) as count
    FROM orders o
    JOIN order_status os ON o.order_status_id = os.id
    GROUP BY os.name
    ORDER BY count DESC
""")
print("\n  By Status:")
for row in cursor.fetchall():
    print(f"    {row[0]:30}: {row[1]:4} orders")

cursor.execute('SELECT COUNT(DISTINCT state) as state_count FROM orders')
state_count = cursor.fetchone()[0]
print(f"\n  Unique States in Orders: {state_count}")

conn.close()

print("\n" + "=" * 100)
print("✅ REFERENCE DATA FIX COMPLETE!")
print("=" * 100)
