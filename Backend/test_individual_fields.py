#!/usr/bin/env python3
"""
Test individual field updates to isolate which field is causing the 500 error
"""

import requests
import json

# Production API details
API_BASE = "https://employee-performance-api-302004244593.asia-south1.run.app/api/v1"
TEAM_ID = 13

# Login token (get a fresh one if needed)
LOGIN_URL = f"{API_BASE}/auth/login"
TEAM_URL = f"{API_BASE}/teams/{TEAM_ID}"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "email": "admin@gmail.com",
        "password": "Admin123!"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        return None

def test_individual_fields():
    """Test updating individual fields to identify which one causes the error"""
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test individual field updates
    test_cases = [
        {"name": "monthlyTarget only", "payload": {"monthlyTarget": 1000}},
        {"name": "step1Score only", "payload": {"step1Score": 0.6}},
        {"name": "step2Score only", "payload": {"step2Score": 0.4}},
        {"name": "singleSeatScore only", "payload": {"singleSeatScore": 1.5}},
        {"name": "name only", "payload": {"name": "Arizona Test"}},
        {"name": "dailyTarget only", "payload": {"dailyTarget": 15}},
        {"name": "empty payload", "payload": {}},
    ]
    
    print("🔍 Testing individual field updates...")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Payload: {json.dumps(test['payload'])}")
        
        try:
            response = requests.put(TEAM_URL, json=test['payload'], headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS")
            else:
                print(f"   ❌ FAILED: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  TIMEOUT (>10s)")
        except Exception as e:
            print(f"   💥 ERROR: {e}")

if __name__ == "__main__":
    test_individual_fields()