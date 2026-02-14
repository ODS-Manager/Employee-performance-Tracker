#!/bin/bash
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
