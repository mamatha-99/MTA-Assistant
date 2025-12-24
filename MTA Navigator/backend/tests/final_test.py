import requests
import uuid
import time

API_URL = "http://localhost:8000/chat"

def run_test_suite():
    print("=== FINAL SYSTEM ACCEPTANCE TEST ===")
    
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    tests = [
        {
            "step": "1. Simple Routing",
            "input": "How do I get from Grand Central to Wall St?",
            "check": lambda r: "Route from Grand Central" in r or "Take 4" in r or "Take 5" in r
        },
        {
            "step": "2. Real-Time Status Check",
            "input": "Any delays on the 4 line?",
            "check": lambda r: "alert" in r.lower() or "no active service alerts" in r.lower()
        },
        {
            "step": "3. Ambiguity Trigger",
            "input": "Go from 86th St to 96th St.",
            "check": lambda r: "Did you mean" in r or "Ambiguous" in r
        },
        {
            "step": "4. Context Resolution (Answering Ambiguity)",
            "input": "The Lexington Avenue one",
            "check": lambda r: "Route from" in r and "86 St" in r
        },
        {
            "step": "5. Invalid Station Handling",
            "input": "Take me to Atlantis.",
            "check": lambda r: "Could not find" in r or "not found" in r
        },
        {
            "step": "6. Next Train Info",
            "input": "When is the next train at Union Square?",
            "check": lambda r: "Route" in r and "min" in r
        }
    ]
    
    passed = 0
    for t in tests:
        print(f"\n--- {t['step']} ---")
        print(f"User: \"{t['input']}\"")
        try:
            start = time.time()
            res = requests.post(API_URL, json={"message": t['input'], "session_id": session_id}, timeout=30)
            dur = time.time() - start
            
            if res.status_code != 200:
                print(f"❌ API Error: {res.status_code}")
                continue
                
            ans = res.json().get("response", "")
            print(f"Agent: {ans.strip()[:200]}...") # Truncate for log
            
            if t['check'](ans):
                print(f"✅ PASSED ({dur:.1f}s)")
                passed += 1
            else:
                print(f"❌ FAILED - Verification conditions not met.")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")

    print(f"\n=== RESULT: {passed}/{len(tests)} Passing ===")

if __name__ == "__main__":
    run_test_suite()
