import requests
import uuid
import time
import json

API_URL = "http://localhost:8000/chat"

def run_specific_test():
    print("=== ASSISTANT MULTI-TURN & SCENARIO TEST ===")
    
    # 1. Ambiguity Test
    print("\n--- TEST 1: Ambiguity (Grand Central -> 82nd St) ---")
    session_id = str(uuid.uuid4())
    query1 = "How do I get from Grand Central to 82nd street?"
    print(f"[User]: \"{query1}\"")
    
    res1 = requests.post(API_URL, json={"message": query1, "session_id": session_id})
    ans1 = res1.json().get("response", "")
    print(f"[Agent]: {ans1}")
    
    # Check for clarification triggers
    if "Did you mean" in ans1 or "multiple matches" in ans1 or "options" in ans1:
        print("   -> Agent asked for clarification (Correct).")
        
        # Turn 2
        query2 = "Grand Central 42nd St"
        print(f"\n[User]: \"{query2}\"")
        res2 = requests.post(API_URL, json={"message": query2, "session_id": session_id})
        ans2 = res2.json().get("response", "")
        print(f"[Agent]: {ans2}")
        
        if "7" in ans2:
             print("✅ Correct Line (7 Train) suggested.")
    else:
        print("   -> Agent routed immediately (Check if correct station picked).")

    # 2. Status Check
    print("\n--- TEST 2: Status Check (7 Train) ---")
    session_id2 = str(uuid.uuid4())
    q_status = "Is there any delay on the 7 train?"
    print(f"[User]: \"{q_status}\"")
    res_s = requests.post(API_URL, json={"message": q_status, "session_id": session_id2})
    ans_s = res_s.json().get("response", "")
    print(f"[Agent]: {ans_s}")
    if "alert" in ans_s.lower() or "service" in ans_s.lower():
        print("✅ Retrieved service status.")

    # 3. Bad Input
    print("\n--- TEST 3: Nonsense Input ---")
    session_id3 = str(uuid.uuid4())
    q_bad = "Take me to Mars"
    print(f"[User]: \"{q_bad}\"")
    res_b = requests.post(API_URL, json={"message": q_bad, "session_id": session_id3})
    ans_b = res_b.json().get("response", "")
    if "not find" in ans_b or "can't assist" in ans_b or "could not" in ans_b.lower():
        print(f"[Agent]: {ans_b}")
        print("✅ Handled gracefully.")
    else:
        print(f"[Agent]: {ans_b}")
        print("⚠️ Potential hallucination.")

if __name__ == "__main__":
    run_specific_test()
