#!/bin/bash
# Quick Setup Script for Employee Performance Tracker
# Run this script to set up the database and start the application

echo "🚀 Employee Performance Tracker - Quick Setup"
echo "=============================================="

# Navigate to backend directory
cd Backend

echo "📊 Setting up database with February 2026 test data..."

# Set database URL environment variable
export DATABASE_URL="sqlite:///./ods_development.db"

# Clean up existing database
rm -f ods_development.db ods_db.sqlite

# Make sure we have proper permissions
chmod 755 .

# Initialize and populate database
echo "   Initializing database..."
python init_database.py

echo "   Adding February 2026 dummy data..."
python add_february_dummy_data.py

# Set final permissions
chmod 666 ods_development.db

echo ""
echo "✅ Database Setup Complete!"
echo ""
echo "📊 Test Data Created:"
echo "   - 400+ orders for February 2026"
echo "   - 16 users (employees, team leads, admins)"
echo "   - 8 teams with members"
echo "   - Daily attendance records"
echo "   - Performance metrics and KPIs"
echo "   - Quality audits and billing data"
echo ""
echo "🔐 Login Credentials:"
echo "   admin / admin123 (Admin)"
echo "   superadmin / superadmin123 (Superadmin)" 
echo "   teamlead / admin123 (Team Lead)"
echo "   employee / admin123 (Employee)"
echo ""
echo "🚀 To start the application:"
echo "   1. Backend: python -m uvicorn main:app --reload"
echo "   2. Frontend: npm start (in separate terminal)"
echo ""
echo "🎯 The dashboard will show February 2026 data for testing!"
echo ""