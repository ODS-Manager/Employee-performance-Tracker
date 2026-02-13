#!/usr/bin/env python3
"""
Test the exact PUT API issue with your production endpoint
"""

import requests
import json

# Your production API details
API_BASE = "https://employee-performance-api-302004244593.asia-south1.run.app/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwicm9sZSI6InN1cGVyYWRtaW4iLCJleHAiOjE3NzA5NjU2NzIsImp0aSI6ImNmY2YzYTRlLThhMmYtNGFjYy1iNmI3LTUwYzM0MDEyYTI0MSIsImlhdCI6MTc3MDk2MjA3MiwidHlwZSI6ImFjY2VzcyJ9.JVOGApu6wRjMri6u4TQek76KfDAPGeAeO419ndbHXvU"
TEAM_ID = 13

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🔍 Testing PUT API issue...")

# Test 1: Get the current team data
print(f"\n1. Getting current data for team {TEAM_ID}...")
try:
    response = requests.get(f"{API_BASE}/teams/{TEAM_ID}", headers=headers, timeout=30)
    print(f"GET Status: {response.status_code}")
    
    if response.status_code == 200:
        team_data = response.json()
        print(f"✅ Team data retrieved successfully")
        print(f"Current values:")
        print(f"  Name: {team_data.get('name')}")
        print(f"  monthlyTarget: {team_data.get('monthlyTarget')}")
        print(f"  step1Score: {team_data.get('step1Score')}")
        print(f"  step2Score: {team_data.get('step2Score')}")
        print(f"  singleSeatScore: {team_data.get('singleSeatScore')}")
    else:
        print(f"❌ GET failed: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ GET error: {e}")
    exit(1)

# Test 2: Test the exact payload that's failing
print(f"\n2. Testing the exact failing payload...")
test_payload = {
    "monthlyTarget": 1000,
    "step1Score": 0.5,
    "step2Score": 0.5,
    "singleSeatScore": 1
}

print(f"Payload: {json.dumps(test_payload, indent=2)}")

try:
    response = requests.put(
        f"{API_BASE}/teams/{TEAM_ID}", 
        headers=headers,
        json=test_payload,
        timeout=30
    )
    
    print(f"PUT Status: {response.status_code}")
    print(f"PUT Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ PUT request successful!")
    else:
        print(f"❌ PUT failed with status {response.status_code}")
        print(f"Error details: {response.text}")
        
        # Try to parse error
        try:
            error_data = response.json()
            print(f"Parsed error: {json.dumps(error_data, indent=2)}")
        except:
            print("Could not parse error as JSON")
            
except requests.Timeout:
    print("❌ PUT request timed out (no response)")
    print("This suggests the server is hanging or there's an infinite loop")
except Exception as e:
    print(f"❌ PUT error: {e}")

# Test 3: Test with minimal payload
print(f"\n3. Testing with minimal payload...")
minimal_payload = {
    "monthlyTarget": team_data.get('monthlyTarget', 1000)
}

print(f"Minimal payload: {json.dumps(minimal_payload, indent=2)}")

try:
    response = requests.put(
        f"{API_BASE}/teams/{TEAM_ID}", 
        headers=headers,
        json=minimal_payload,
        timeout=15
    )
    
    print(f"Minimal PUT Status: {response.status_code}")
    print(f"Minimal PUT Response: {response.text}")
    
except requests.Timeout:
    print("❌ Minimal PUT also timed out")
except Exception as e:
    print(f"❌ Minimal PUT error: {e}")

# Test 4: Test with snake_case (to see if our mapping works)
print(f"\n4. Testing with snake_case fields...")
snake_case_payload = {
    "monthly_target": 1000,
    "step1_score": 0.5,
    "step2_score": 0.5,
    "single_seat_score": 1
}

print(f"Snake_case payload: {json.dumps(snake_case_payload, indent=2)}")

try:
    response = requests.put(
        f"{API_BASE}/teams/{TEAM_ID}", 
        headers=headers,
        json=snake_case_payload,
        timeout=15
    )
    
    print(f"Snake_case PUT Status: {response.status_code}")
    print(f"Snake_case PUT Response: {response.text}")
    
except requests.Timeout:
    print("❌ Snake_case PUT also timed out")
except Exception as e:
    print(f"❌ Snake_case PUT error: {e}")

print("\n📊 Summary:")
print("If all requests are timing out, the issue is likely:")
print("1. Infinite loop in the field mapping logic")
print("2. Database deadlock or long-running query")
print("3. Validation error causing server hang")
print("4. Our field mapping code has a bug")