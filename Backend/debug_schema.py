#!/usr/bin/env python3
"""
Debug script to test TeamUpdate schema validation locally
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.schemas.team import TeamUpdate
import json

def test_schema_validation():
    """Test if the TeamUpdate schema can handle the payload that's causing 500 errors"""
    
    print("🔍 Testing TeamUpdate schema validation...")
    
    # Test the exact payload that's causing issues in production
    test_payloads = [
        {
            "name": "Test 1: Original failing payload",
            "payload": {
                "monthlyTarget": 1000,
                "step1Score": 0.5,
                "step2Score": 0.5,
                "singleSeatScore": 1
            }
        },
        {
            "name": "Test 2: Minimal payload",
            "payload": {
                "monthlyTarget": 1000
            }
        },
        {
            "name": "Test 3: Snake case payload",
            "payload": {
                "monthly_target": 1000,
                "step1_score": 0.5,
                "step2_score": 0.5,
                "single_seat_score": 1
            }
        },
        {
            "name": "Test 4: Empty payload",
            "payload": {}
        }
    ]
    
    for test in test_payloads:
        print(f"\n{test['name']}:")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            # Test schema validation
            team_data = TeamUpdate(**test['payload'])
            print(f"✅ Schema validation successful")
            
            # Test model_dump with by_alias=False
            update_data = team_data.model_dump(exclude_unset=True, exclude={'states', 'products', 'fa_names'}, by_alias=False)
            print(f"✅ model_dump successful: {update_data}")
            
            # Test field extraction (like in the actual endpoint)
            print(f"Fields that would be updated:")
            for field, value in update_data.items():
                print(f"  {field}: {value} (type: {type(value).__name__})")
                
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_schema_validation()