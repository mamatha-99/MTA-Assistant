import requests
import json
import time

API_URL = "http://localhost:8000/chat"

TEST_CASES = [
    {
        "name": "Standard Route (Manhattan)",
        "message": "How do I get from Grand Central to Wall St?",
        "expect_keywords": ["Grand Central", "Wall St", "train"]
    },
    {
        "name": "Ambiguous Station Name",
        "message": "Route from 86th St to 96th St",
        "expect_keywords": ["Route", "from", "to"] 
        # Note: We rely on Fuzzy Matcher picking *something*. 
        # A smart system would ask for clarification, but our tool blindly picks the best match (e.g. 86th St Lex).
        # We verify it doesn't crash.
    },
    {
        "name": "Next Train Lookup",
        "message": "When is the next train at Grand Central?",
        "expect_keywords": ["Route", "min"] # Should allow for "No trains" if late night, but usually "Route 4..."
    },
    {
        "name": "Status Check",
        "message": "Are there any subway delays right now?",
        "expect_keywords": ["Service Alert", "No active service alerts", "delayed", "planned"]
    },
    {
        "name": "Long Haul (Queens -> Brooklyn)",
        "message": "Guide me from Flushing Main St to Coney Island",
        "expect_keywords": ["minutes", "Steps", "Route"]
    },
    {
        "name": "Invalid Station",
        "message": "How do I get from Gotham City to Atlantis?",
        "expect_keywords": ["Could not find", "not found"]
    }
]

def run_stress_test():
    print("=== NYC SUBWAY SYSTEM STRESS TEST ===")
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] Testing: {case['name']}")
        print(f"   Query: \"{case['message']}\"")
        
        start_t = time.time()
        try:
            res = requests.post(API_URL, json={"message": case['message']}, timeout=20)
            duration = time.time() - start_t
            
            if res.status_code != 200:
                print(f"   ❌ FAILED: Status {res.status_code}")
                print(f"   Output: {res.text}")
                failed += 1
                continue
                
            data = res.json()
            response_text = data.get("response", "")
            
            # Validation
            kw_found = [k for k in case['expect_keywords'] if k.lower() in response_text.lower()]
            
            if kw_found:
                print(f"   ✅ PASSED ({duration:.1f}s)")
                print(f"      Response: {response_text}")
                passed += 1
            else:
                print(f"   ⚠️ WARNING: Keywords {case['expect_keywords']} not found.")
                print(f"      Full Response: {response_text}")
                # We count as soft fail
                failed += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1

    print(f"\n=== SUMMARY: {passed} PASSED, {failed} FAILED ===")

if __name__ == "__main__":
    run_stress_test()
