#!/usr/bin/env python3
"""
Test that the PUT endpoint actually updates the team data
"""

import requests
import json

# Production API details
API_BASE = "https://employee-performance-api-302004244593.asia-south1.run.app/api/v1"
TEAM_ID = 13

# Login token (get a fresh one if needed)
LOGIN_URL = f"{API_BASE}/auth/login"
TEAMS_URL = f"{API_BASE}/teams"
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

def test_team_update():
    """Test that PUT endpoint actually updates team data"""
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get initial team data
    print("1. Getting initial team data...")
    response = requests.get(TEAM_URL, headers=headers)
    if response.status_code == 200:
        initial_data = response.json()
        print(f"   Initial monthlyTarget: {initial_data.get('monthlyTarget')}")
        print(f"   Initial step1Score: {initial_data.get('step1Score')}")
        print(f"   Initial modifiedAt: {initial_data.get('modifiedAt')}")
    else:
        print(f"   ❌ Failed to get initial data: {response.status_code}")
        return
    
    # Update team with new values
    print("\n2. Updating team data...")
    update_payload = {
        "monthlyTarget": 1500,
        "step1Score": 0.75,
        "step2Score": 0.65
    }
    
    response = requests.put(TEAM_URL, json=update_payload, headers=headers)
    print(f"   PUT Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ PUT request successful")
    else:
        print(f"   ❌ PUT request failed: {response.text}")
        return
    
    # Get updated team data to verify changes
    print("\n3. Verifying changes...")
    response = requests.get(TEAM_URL, headers=headers)
    if response.status_code == 200:
        updated_data = response.json()
        print(f"   Updated monthlyTarget: {updated_data.get('monthlyTarget')}")
        print(f"   Updated step1Score: {updated_data.get('step1Score')}")
        print(f"   Updated step2Score: {updated_data.get('step2Score')}")
        print(f"   Updated modifiedAt: {updated_data.get('modifiedAt')}")
        
        # Check if data actually changed
        if (updated_data.get('monthlyTarget') == 1500 and 
            updated_data.get('step1Score') == 0.75 and
            updated_data.get('step2Score') == 0.65):
            print("\n✅ SUCCESS: Team data was actually updated!")
        else:
            print("\n❌ FAILURE: Team data was not updated properly")
            print(f"Expected monthlyTarget: 1500, got: {updated_data.get('monthlyTarget')}")
            print(f"Expected step1Score: 0.75, got: {updated_data.get('step1Score')}")
            print(f"Expected step2Score: 0.65, got: {updated_data.get('step2Score')}")
    else:
        print(f"   ❌ Failed to get updated data: {response.status_code}")

if __name__ == "__main__":
    test_team_update()