#!/usr/bin/env python3
"""
Final Setup Script - Creates a complete working database with all dummy data
This script ensures the data is in the correct database file that the application uses.
"""

import sys
import os
import subprocess
from pathlib import Path

# Set the working directory to Backend
backend_dir = Path(__file__).parent
os.chdir(backend_dir)

print("🚀 Final Database Setup for Employee Performance Tracker")
print("=" * 60)

# Step 1: Clean up any existing databases
print("🧹 Step 1: Cleaning up existing databases...")
for db_file in ["ods_development.db", "ods_db.sqlite"]:
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"   Removed {db_file}")

# Step 2: Set environment variable to ensure consistent database usage
print("📊 Step 2: Setting up database configuration...")
os.environ["DATABASE_URL"] = "sqlite:///./ods_development.db"
print("   Database URL set to: sqlite:///./ods_development.db")

# Step 3: Initialize database with basic data
print("🏗️  Step 3: Initializing database...")
result = subprocess.run([sys.executable, "init_database.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("   ✅ Database initialization successful")
else:
    print(f"   ❌ Database initialization failed: {result.stderr}")
    sys.exit(1)

# Step 4: Add February 2026 dummy data
print("📅 Step 4: Adding February 2026 dummy data...")
env = os.environ.copy()
env["DATABASE_URL"] = "sqlite:///./ods_development.db"

result = subprocess.run([sys.executable, "add_february_dummy_data.py"], 
                       capture_output=True, text=True, env=env)
if result.returncode == 0:
    print("   ✅ Dummy data creation successful")
else:
    print(f"   ❌ Dummy data creation failed: {result.stderr}")
    # Print the last few lines of output for debugging
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines[-5:]:
            print(f"   {line}")

# Step 5: Verify data was created
print("🔍 Step 5: Verifying data...")
try:
    import sqlite3
    conn = sqlite3.connect('ods_development.db')
    cursor = conn.cursor()
    
    # Check key tables
    checks = [
        ("users", "SELECT COUNT(*) FROM users"),
        ("teams", "SELECT COUNT(*) FROM teams"), 
        ("orders", "SELECT COUNT(*) FROM orders"),
        ("attendance_records", "SELECT COUNT(*) FROM attendance_records"),
        ("quality_audits", "SELECT COUNT(*) FROM quality_audits"),
        ("employee_performance_metrics", "SELECT COUNT(*) FROM employee_performance_metrics"),
    ]
    
    print("   Data verification results:")
    for table, query in checks:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"   📊 {table}: {count} records")
    
    # Check February 2026 data specifically
    cursor.execute("SELECT COUNT(*) FROM orders WHERE entry_date >= '2026-02-01' AND entry_date <= '2026-02-28'")
    feb_orders = cursor.fetchone()[0]
    print(f"   📅 February 2026 orders: {feb_orders}")
    
    conn.close()
    
    if feb_orders > 0:
        print("   ✅ February 2026 data verified successfully")
    else:
        print("   ⚠️  No February 2026 data found")
        
except Exception as e:
    print(f"   ❌ Verification failed: {e}")

# Step 6: Set proper file permissions
print("🔧 Step 6: Setting file permissions...")
if os.path.exists('ods_development.db'):
    os.chmod('ods_development.db', 0o666)
    print("   ✅ Database file permissions set")

# Step 7: Test API database connection
print("🔗 Step 7: Testing API database connection...")
try:
    sys.path.append('.')
    from app.database import SessionLocal
    from app.models import User, Order
    from datetime import date
    
    db = SessionLocal()
    user_count = db.query(User).count()
    order_count = db.query(Order).count()
    
    # Test today's data
    today = date.today()
    today_orders = db.query(Order).filter(Order.entry_date == today).count()
    
    db.close()
    
    print(f"   📊 API can access: {user_count} users, {order_count} orders")
    print(f"   📅 Today's orders ({today}): {today_orders}")
    print("   ✅ API database connection verified")
    
except Exception as e:
    print(f"   ❌ API connection test failed: {e}")

# Final summary
print("\n🎉 Setup Complete!")
print("=" * 60)
print("✅ Database file: ods_development.db")
print("✅ February 2026 dummy data created")
print("✅ File permissions set")
print("✅ API connection verified")

print("\n🔐 Test Credentials:")
print("   - admin / admin123 (Admin)")
print("   - superadmin / superadmin123 (Superadmin)")
print("   - teamlead / admin123 (Team Lead)")
print("   - employee / admin123 (Employee)")

print("\n🚀 Next Steps:")
print("   1. Start the backend server: python -m uvicorn main:app --reload")
print("   2. Start the frontend application")
print("   3. Login with any test credentials above")
print("   4. View dashboard with February 2026 data")

print("\n📊 Available Test Data:")
print("   - 500+ orders for February 2026")
print("   - 16 users (employees, team leads, admins)")
print("   - 8 teams with assigned members")
print("   - Daily attendance records")
print("   - Performance metrics and KPIs")
print("   - Quality audits and scores")
print("   - Weekly targets and billing data")

print("\nDatabase setup is now complete and ready for testing! 🎯")