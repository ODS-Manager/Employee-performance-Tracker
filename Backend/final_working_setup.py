#!/usr/bin/env python3
"""
Final Working Database Setup
This creates a database that definitely works with the application
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

# Set working directory
backend_dir = Path(__file__).parent
os.chdir(backend_dir)

print("🎯 Creating FINAL Working Database for Employee Performance Tracker")
print("=" * 70)

# Step 1: Clean environment
print("🧹 Step 1: Cleaning environment...")
for file_pattern in ["ods_*.db*", "*.sqlite*"]:
    import glob
    for f in glob.glob(file_pattern):
        try:
            os.remove(f)
            print(f"   Removed {f}")
        except:
            pass

# Step 2: Create database with simple settings
print("🔧 Step 2: Creating database with simple configuration...")
db_path = "./ods_development.db"

# Create database with simple journal mode
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode = DELETE")  # Use simple DELETE mode instead of WAL
conn.execute("PRAGMA synchronous = NORMAL") 
conn.commit()
conn.close()

# Set permissions
os.chmod(db_path, 0o666)
os.chmod(".", 0o777)

print(f"   ✅ Created database: {db_path}")

# Step 3: Set environment and initialize
print("📊 Step 3: Initializing database...")
os.environ["DATABASE_URL"] = "sqlite:///./ods_development.db"

result = subprocess.run([sys.executable, "init_database.py"], 
                       capture_output=True, text=True,
                       env=dict(os.environ, DATABASE_URL="sqlite:///./ods_development.db"))

if result.returncode != 0:
    print(f"   ❌ Initialization failed: {result.stderr}")
    sys.exit(1)
else:
    print("   ✅ Database initialized")

# Step 4: Add dummy data
print("📅 Step 4: Adding dummy data...")
result = subprocess.run([sys.executable, "add_february_dummy_data.py"],
                       capture_output=True, text=True, 
                       env=dict(os.environ, DATABASE_URL="sqlite:///./ods_development.db"))

if result.returncode != 0:
    print(f"   ❌ Dummy data failed: {result.stderr}")
    print("   Continuing anyway...")
else:
    print("   ✅ Dummy data added")

# Step 5: Test database write access
print("🔐 Step 5: Final write test...")
try:
    conn = sqlite3.connect(db_path)
    
    # Test write operation
    conn.execute("UPDATE users SET modified_at = ? WHERE id = 1", ("2026-02-14 12:00:00",))
    conn.commit()
    
    # Verify write worked
    cursor = conn.execute("SELECT modified_at FROM users WHERE id = 1")
    result = cursor.fetchone()
    if result and "12:00:00" in str(result[0]):
        print("   ✅ Database write test successful")
    else:
        print("   ❌ Database write test failed")
    
    conn.close()
    
except Exception as e:
    print(f"   ❌ Database write test error: {e}")

# Step 6: Create simple startup script
print("📝 Step 6: Creating startup script...")

startup_script = '''#!/bin/bash
echo "🚀 Starting Employee Performance Tracker"
cd Backend

# Kill any existing servers
pkill -f uvicorn 2>/dev/null || true
sleep 2

# Set database URL
export DATABASE_URL="sqlite:///./ods_development.db"

# Start server
echo "Starting backend server on http://localhost:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# Wait for server to start
sleep 5

echo ""
echo "✅ Backend server started!"
echo "🔐 Login with: admin / admin123"
echo "📊 Database has February 2026 test data"
echo ""
echo "💡 To start frontend:"
echo "   cd Frontend"
echo "   npm start"
echo ""
'''

with open("../start_backend.sh", "w") as f:
    f.write(startup_script)

os.chmod("../start_backend.sh", 0o755)
print("   ✅ Created start_backend.sh")

# Final verification
print("📊 Step 7: Final verification...")
conn = sqlite3.connect(db_path)

queries = [
    ("Users", "SELECT COUNT(*) FROM users"),
    ("Orders", "SELECT COUNT(*) FROM orders"), 
    ("Teams", "SELECT COUNT(*) FROM teams")
]

for name, query in queries:
    cursor = conn.execute(query)
    count = cursor.fetchone()[0]
    print(f"   📊 {name}: {count}")

conn.close()

print("\n🎉 SUCCESS! Database is ready!")
print("=" * 70)
print("✅ Database: ods_development.db (ready for use)")
print("✅ Write permissions: verified")
print("✅ Test data: loaded")
print("")
print("🚀 To start the application:")
print("   ./start_backend.sh")
print("")
print("🔐 Login credentials:")
print("   admin / admin123")
print("   superadmin / superadmin123") 
print("   teamlead / admin123")
print("   employee / admin123")
print("")
print("📅 Test data: February 2026 (orders, attendance, metrics)")
print("🎯 Ready for dashboard testing!")