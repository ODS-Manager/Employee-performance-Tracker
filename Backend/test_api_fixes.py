#!/usr/bin/env python3
"""
Test script to verify the API fixes for team management
This script tests both the team list endpoint and the team update endpoint
"""

import requests
import json
import sys
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"  # Change this to your server URL
API_BASE = f"{BASE_URL}/api/v1"

def login(username: str, password: str) -> str:
    """Login and get access token"""
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{API_BASE}/auth/login", data=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_team_list(token: str) -> bool:
    """Test team list endpoint to ensure states and products are displayed"""
    print("\n🔍 Testing team list endpoint...")
    
    headers = get_headers(token)
    response = requests.get(f"{API_BASE}/teams", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Team list failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    teams = data.get("items", [])
    
    if not teams:
        print("⚠️  No teams found")
        return False
    
    print(f"✅ Found {len(teams)} teams")
    
    # Check if teams have states and products (should not be empty arrays)
    teams_with_data = 0
    for team in teams[:3]:  # Check first 3 teams
        team_name = team.get("name", "Unknown")
        states = team.get("states", [])
        products = team.get("products", [])
        fa_names = team.get("fa_names", [])
        
        print(f"  Team: {team_name}")
        print(f"    States: {len(states)} - {[s.get('name') for s in states[:2]]}")
        print(f"    Products: {len(products)} - {[p.get('name') for p in products[:2]]}")
        print(f"    FA Names: {len(fa_names)}")
        
        if states or products:
            teams_with_data += 1
    
    if teams_with_data > 0:
        print(f"✅ {teams_with_data} teams have states/products data")
        return True
    else:
        print("❌ No teams have states/products data - fix may not be working")
        return False

def test_team_update(token: str, team_id: int) -> bool:
    """Test team update endpoint with camelCase fields"""
    print(f"\n✏️  Testing team update endpoint for team {team_id}...")
    
    headers = get_headers(token)
    
    # First get the current team data
    response = requests.get(f"{API_BASE}/teams/{team_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Could not fetch team {team_id}: {response.status_code}")
        return False
    
    original_team = response.json()
    original_target = original_team.get("monthlyTarget", 100)
    
    # Test update with camelCase fields
    update_data = {
        "name": original_team.get("name"),
        "monthlyTarget": original_target + 1,  # camelCase field
        "dailyTarget": 25,                     # camelCase field 
        "step1Score": 85,                      # camelCase field
        "step2Score": 90                       # camelCase field
    }
    
    print(f"  Updating with data: {update_data}")
    
    response = requests.put(
        f"{API_BASE}/teams/{team_id}", 
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        updated_team = response.json()
        new_target = updated_team.get("monthlyTarget")
        
        if new_target == original_target + 1:
            print(f"✅ Update successful: monthlyTarget changed from {original_target} to {new_target}")
            
            # Restore original value
            restore_data = {"monthlyTarget": original_target}
            requests.put(f"{API_BASE}/teams/{team_id}", headers=headers, json=restore_data)
            print("  Restored original values")
            return True
        else:
            print(f"❌ Update failed: monthlyTarget should be {original_target + 1}, got {new_target}")
            return False
    else:
        print(f"❌ Update failed: {response.status_code} - {response.text}")
        return False

def test_authentication() -> bool:
    """Test authentication with new credentials"""
    print("\n🔐 Testing authentication...")
    
    # Test credentials created in our fix
    test_credentials = [
        ("admin", "admin123"),
        ("superadmin", "superadmin123"),
        ("teamlead", "admin123"),
        ("employee", "admin123")
    ]
    
    success_count = 0
    for username, password in test_credentials:
        token = login(username, password)
        if token:
            print(f"✅ Login successful for {username}")
            success_count += 1
        else:
            print(f"❌ Login failed for {username}")
    
    return success_count > 0

def main():
    """Main test function"""
    print("🚀 Starting API Fix Verification Tests")
    print("=" * 50)
    
    # Test authentication first
    auth_success = test_authentication()
    if not auth_success:
        print("❌ Authentication tests failed - cannot proceed with API tests")
        print("\nPlease ensure:")
        print("1. Database is running and accessible")
        print("2. User authentication fix SQL has been applied")
        print("3. Backend server is running on", BASE_URL)
        return False
    
    # Get token for API tests (use admin account)
    token = login("admin", "admin123")
    if not token:
        token = login("superadmin", "superadmin123")
    
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    print(f"✅ Got authentication token")
    
    # Test team list endpoint
    list_success = test_team_list(token)
    
    # Test team update endpoint (use team ID 1 if available)
    update_success = test_team_update(token, team_id=1)
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Authentication: {'✅ PASS' if auth_success else '❌ FAIL'}")
    print(f"Team List (states/products): {'✅ PASS' if list_success else '❌ FAIL'}")
    print(f"Team Update (camelCase): {'✅ PASS' if update_success else '❌ FAIL'}")
    
    if list_success and update_success:
        print("\n🎉 All API fixes working correctly!")
        return True
    else:
        print("\n⚠️  Some tests failed - please check the backend logs")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)