import requests
import json

API_URL = "http://localhost:8000/chat"

def debug_ambiguity():
    print("Testing Ambiguity Case: 'Route from 86th St to 96th St'")
    
    # 86th St could be:
    # - 86 St (1 Line) - ID 122
    # - 86 St (4/5/6 Line) - ID 626
    # - 86 St (N/Q/R - Brooklyn) - ID R44 ? (Wait, N line 86 St is Brooklyn/Gravesend)
    # - 86 St (B/C - Central Park West) - ID A20
    #
    # 96th St could be:
    # - 96 St (1/2/3) - ID 120
    # - 96 St (6) - ID 625
    # - 96 St (BC) - ID A19
    # - 96 St (Q - Second Ave) - ID Q05
    
    payload = {"message": "Route from 86th St to 96th St"}
    
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        print(f"\nStatus: {res.status_code}")
        print("Response Body:")
        print(res.json().get("response"))
        
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    debug_ambiguity()
