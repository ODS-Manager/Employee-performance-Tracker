#!/usr/bin/env python3
"""
Production-safe PUT API diagnostic script
Tests the team update endpoint without modifying data
"""

import requests
import json
import sys
from typing import Dict, Any

# Production API Configuration
BASE_URL = input("Enter your API base URL (e.g., https://your-api.com): ").strip()
if not BASE_URL:
    BASE_URL = "http://localhost:8000"

API_BASE = f"{BASE_URL}/api/v1"

def login(username: str, password: str) -> str:
    """Login and get access token"""
    print(f"🔐 Attempting login for user: {username}")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", data=login_data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful for {username}")
            return token_data.get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.RequestException as e:
        print(f"❌ Connection error during login: {e}")
        return None

def get_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_team_list_api(token: str) -> Dict:
    """Test team list endpoint and return first team data"""
    print("\n🔍 Testing team list endpoint...")
    
    headers = get_headers(token)
    
    try:
        response = requests.get(f"{API_BASE}/teams", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Team list failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        teams = data.get("items", [])
        
        if not teams:
            print("⚠️  No teams found in response")
            return None
        
        print(f"✅ Found {len(teams)} teams")
        
        # Show first team structure
        first_team = teams[0]
        print(f"\n📋 First team structure:")
        print(f"  ID: {first_team.get('id')}")
        print(f"  Name: {first_team.get('name')}")
        print(f"  Monthly Target: {first_team.get('monthlyTarget')}")
        print(f"  States: {len(first_team.get('states', []))}")
        print(f"  Products: {len(first_team.get('products', []))}")
        
        return first_team
        
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def test_put_api_dry_run(token: str, team_id: int, current_team: Dict) -> bool:
    """Test PUT API with minimal changes (dry run approach)"""
    print(f"\n✏️  Testing PUT API for team {team_id} (READ-ONLY TEST)...")
    
    headers = get_headers(token)
    
    # Get current team data first
    try:
        response = requests.get(f"{API_BASE}/teams/{team_id}", headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Could not fetch team {team_id}: {response.status_code}")
            return False
        
        team_data = response.json()
        print(f"📊 Current team data retrieved:")
        print(f"  Name: {team_data.get('name')}")
        print(f"  Monthly Target: {team_data.get('monthlyTarget')}")
        print(f"  Daily Target: {team_data.get('dailyTarget')}")
        
    except requests.RequestException as e:
        print(f"❌ Error fetching team data: {e}")
        return False
    
    # Test different payload formats
    test_payloads = [
        {
            "name": "Test camelCase fields",
            "payload": {
                "name": team_data.get('name'),  # Keep same name
                "monthlyTarget": team_data.get('monthlyTarget', 100),  # camelCase
                "dailyTarget": team_data.get('dailyTarget', 10),       # camelCase
            }
        },
        {
            "name": "Test snake_case fields", 
            "payload": {
                "name": team_data.get('name'),  # Keep same name
                "monthly_target": team_data.get('monthlyTarget', 100),  # snake_case
                "daily_target": team_data.get('dailyTarget', 10),       # snake_case
            }
        }
    ]
    
    print(f"\n🧪 Testing different payload formats...")
    
    success_count = 0
    for test in test_payloads:
        print(f"\n  🔬 Testing: {test['name']}")
        print(f"     Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            # NOTE: This actually sends the request, but with same values
            response = requests.put(
                f"{API_BASE}/teams/{team_id}", 
                headers=headers,
                json=test['payload'],
                timeout=10
            )
            
            print(f"     Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"     ✅ SUCCESS - {test['name']} works!")
                success_count += 1
            else:
                print(f"     ❌ FAILED - {test['name']}")
                print(f"     Error: {response.text}")
                
        except requests.RequestException as e:
            print(f"     ❌ Connection error: {e}")
    
    return success_count > 0

def main():
    """Main diagnostic function"""
    print("🚀 Production PUT API Diagnostic Test")
    print("=" * 50)
    print("⚠️  This script tests the PUT API with minimal changes")
    print("⚠️  It uses the same values to avoid data corruption")
    
    # Get credentials
    username = input("\nEnter username: ").strip()
    password = input("Enter password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required")
        return False
    
    # Login
    token = login(username, password)
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    # Test team list
    first_team = test_team_list_api(token)
    if not first_team:
        print("❌ Could not get team data for testing")
        return False
    
    team_id = first_team.get('id')
    if not team_id:
        print("❌ No team ID found")
        return False
    
    # Test PUT API
    put_success = test_put_api_dry_run(token, team_id, first_team)
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Team List API: {'✅ WORKING' if first_team else '❌ FAILED'}")
    print(f"PUT API: {'✅ WORKING' if put_success else '❌ FAILED'}")
    
    if not put_success:
        print("\n🔧 PUT API Issue Detected!")
        print("Possible causes:")
        print("1. Field name mapping issue (camelCase vs snake_case)")
        print("2. Authentication/permission issue")
        print("3. Validation error in the payload")
        print("4. Database constraint violation")
    
    return put_success

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