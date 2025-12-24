#!/usr/bin/env python3
"""
Comprehensive QA Testing Script for NYC Subway Assistant
Tests all major functionalities: Navigation, Schedules, Alerts, Context, Edge Cases
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
API_BASE = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE}/chat"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestResult:
    def __init__(self, test_id: str, description: str, query: str, expected: str):
        self.test_id = test_id
        self.description = description
        self.query = query
        self.expected = expected
        self.response = None
        self.passed = None
        self.notes = ""
        self.execution_time = 0

class QATester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.session_id = str(uuid.uuid4())
        
    def send_message(self, message: str, new_session: bool = False) -> Tuple[str, float]:
        """Send a message to the chatbot and return response + execution time"""
        if new_session:
            self.session_id = str(uuid.uuid4())
            
        start_time = time.time()
        
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=60)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                return response.json().get("response", ""), execution_time
            else:
                return f"ERROR: HTTP {response.status_code}", execution_time
                
        except requests.exceptions.ConnectionError:
            return "ERROR: Cannot connect to server. Is it running on port 8000?", 0
        except Exception as e:
            return f"ERROR: {str(e)}", 0
    
    def run_test(self, test_id: str, description: str, query: str, 
                 expected_keywords: List[str], fail_keywords: List[str] = None,
                 new_session: bool = True) -> TestResult:
        """Run a single test case"""
        
        result = TestResult(test_id, description, query, ", ".join(expected_keywords))
        
        print(f"\n{Colors.OKBLUE}[{test_id}] {description}{Colors.ENDC}")
        print(f"Query: {Colors.OKCYAN}\"{query}\"{Colors.ENDC}")
        
        response, exec_time = self.send_message(query, new_session=new_session)
        result.response = response
        result.execution_time = exec_time
        
        # Check if response contains expected keywords
        passed = True
        missing_keywords = []
        
        for keyword in expected_keywords:
            if keyword.lower() not in response.lower():
                passed = False
                missing_keywords.append(keyword)
        
        # Check for failure keywords
        if fail_keywords:
            for fail_kw in fail_keywords:
                if fail_kw.lower() in response.lower():
                    passed = False
                    result.notes += f"Contains failure keyword: '{fail_kw}'. "
        
        if missing_keywords:
            result.notes += f"Missing keywords: {missing_keywords}. "
        
        result.passed = passed
        
        # Print result
        if passed:
            print(f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC} ({exec_time:.2f}s)")
        else:
            print(f"{Colors.FAIL}✗ FAILED{Colors.ENDC} ({exec_time:.2f}s)")
            print(f"Notes: {result.notes}")
        
        print(f"Response preview: {response[:200]}...")
        
        self.results.append(result)
        return result
    
    def run_conversation_test(self, test_id: str, description: str, 
                             messages: List[Dict[str, any]]) -> TestResult:
        """Run a multi-turn conversation test"""
        
        print(f"\n{Colors.OKBLUE}[{test_id}] {description}{Colors.ENDC}")
        
        # Start with new session
        self.session_id = str(uuid.uuid4())
        
        all_passed = True
        responses = []
        
        for i, msg in enumerate(messages):
            query = msg['query']
            expected = msg.get('expected', [])
            fail_keywords = msg.get('fail', [])
            
            print(f"\n  Turn {i+1}: {Colors.OKCYAN}\"{query}\"{Colors.ENDC}")
            
            response, exec_time = self.send_message(query, new_session=False)
            responses.append(response)
            
            # Check expectations
            turn_passed = True
            for keyword in expected:
                if keyword.lower() not in response.lower():
                    turn_passed = False
                    all_passed = False
                    print(f"  {Colors.FAIL}✗ Missing: '{keyword}'{Colors.ENDC}")
            
            if fail_keywords:
                for fail_kw in fail_keywords:
                    if fail_kw.lower() in response.lower():
                        turn_passed = False
                        all_passed = False
                        print(f"  {Colors.FAIL}✗ Contains failure keyword: '{fail_kw}'{Colors.ENDC}")
            
            if turn_passed:
                print(f"  {Colors.OKGREEN}✓ Turn passed{Colors.ENDC}")
            
            print(f"  Response: {response[:150]}...")
        
        # Create result
        result = TestResult(test_id, description, "Multi-turn", "See conversation")
        result.response = "\n\n".join([f"Turn {i+1}: {r}" for i, r in enumerate(responses)])
        result.passed = all_passed
        
        if all_passed:
            print(f"\n{Colors.OKGREEN}✓ CONVERSATION PASSED{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}✗ CONVERSATION FAILED{Colors.ENDC}")
        
        self.results.append(result)
        return result
    
    def print_summary(self):
        """Print test summary"""
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.HEADER}TEST SUMMARY{Colors.ENDC}")
        print("="*80)
        
        print(f"\nTotal Tests: {total}")
        print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}")
        print(f"Pass Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print(f"\n{Colors.FAIL}FAILED TESTS:{Colors.ENDC}")
            for r in self.results:
                if not r.passed:
                    print(f"  [{r.test_id}] {r.description}")
                    print(f"    Query: \"{r.query}\"")
                    print(f"    Notes: {r.notes}")
        
        print("\n" + "="*80)
    
    def export_report(self, filename: str = "qa_test_results.json"):
        """Export detailed results to JSON"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
            },
            "tests": []
        }
        
        for r in self.results:
            report["tests"].append({
                "test_id": r.test_id,
                "description": r.description,
                "query": r.query,
                "expected": r.expected,
                "response": r.response,
                "passed": r.passed,
                "notes": r.notes,
                "execution_time": r.execution_time
            })
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.OKGREEN}Report exported to: {filename}{Colors.ENDC}")

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("="*80)
    print("NYC SUBWAY ASSISTANT - COMPREHENSIVE QA TEST SUITE")
    print("="*80)
    print(f"{Colors.ENDC}\n")
    
    tester = QATester()
    
    # ============================================================================
    # CATEGORY A: NAVIGATION / ROUTING TESTS
    # ============================================================================
    print(f"\n{Colors.BOLD}{Colors.HEADER}═══ CATEGORY A: NAVIGATION / ROUTING TESTS ═══{Colors.ENDC}")
    
    tester.run_test(
        "NAV-001", 
        "Basic route planning",
        "How do I get from Times Square to Grand Central?",
        ["route", "train", "Grand Central", "Times", "minute"]
    )
    
    tester.run_test(
        "NAV-002",
        "Route with transfer",
        "How do I get from Brooklyn Bridge to 86th St on Lexington?",
        ["route", "train", "transfer", "Brooklyn"]
    )
    
    tester.run_test(
        "NAV-003",
        "Colloquial station names",
        "From GC to Penn Station",
        ["route", "train"],
        fail_keywords=["not found", "Could not find"]
    )
    
    tester.run_test(
        "NAV-004",
        "Complex multi-transfer route",
        "From Coney Island to Yankee Stadium",
        ["route", "train"]
    )
    
    tester.run_test(
        "NAV-005",
        "Invalid station",
        "How do I get from Jupiter to Mars?",
        ["Could not find", "not found"],
        fail_keywords=["route from Jupiter"]  # Should NOT hallucinate a route
    )
    
    tester.run_test(
        "NAV-006",
        "Route duration display",
        "What's the fastest route from Wall St to Harlem-125th?",
        ["route", "min", "train"]
    )
    
    # ============================================================================
    # CATEGORY B: TRAIN SCHEDULE / REAL-TIME DATA TESTS
    # ============================================================================
    print(f"\n{Colors.BOLD}{Colors.HEADER}═══ CATEGORY B: TRAIN SCHEDULE / REAL-TIME DATA TESTS ═══{Colors.ENDC}")
    
    tester.run_test(
        "SCH-001",
        "Next train at specific station",
        "When is the next 7 train at Grand Central?",
        ["train", "Grand Central"],
        fail_keywords=["Could not find"]
    )
    
    tester.run_test(
        "SCH-002",
        "Multiple lines at station",
        "Show me the next trains at Union Square",
        ["Union Square"],
        fail_keywords=["Could not find", "not found"]
    )
    
    tester.run_test(
        "SCH-003",
        "Q train at specific station",
        "Next Q train at Times Square",
        ["Q", "Times Square"]
    )
    
    # ============================================================================
    # CATEGORY C: SERVICE ALERT TESTS
    # ============================================================================
    print(f"\n{Colors.BOLD}{Colors.HEADER}═══ CATEGORY C: SERVICE ALERT TESTS ═══{Colors.ENDC}")
    
    tester.run_test(
        "ALE-001",
        "General alerts query",
        "Are there any service alerts?",
        ["alert", "service"]
    )
    
    tester.run_test(
        "ALE-002",
        "Line-specific alert check",
        "Any delays on the L train?",
        ["L"]
    )
    
    # ============================================================================
    # CATEGORY D: CONVERSATIONAL CONTEXT TESTS
    # ============================================================================
    print(f"\n{Colors.BOLD}{Colors.HEADER}═══ CATEGORY D: CONVERSATIONAL CONTEXT TESTS ═══{Colors.ENDC}")
    
    tester.run_conversation_test(
        "CTX-001",
        "Follow-up clarification for ambiguous station",
        [
            {
                "query": "How do I get from 86th St to Times Square?",
                "expected": ["ambiguous", "86", "which"],
            },
            {
                "query": "The one on Lexington Avenue",
                "expected": ["route", "train", "Times"],
            }
        ]
    )
    
    tester.run_conversation_test(
        "CTX-002",
        "Multi-turn planning with incomplete info",
        [
            {
                "query": "I'm at Times Square",
                "expected": ["where", "destination", "going"],
            },
            {
                "query": "I want to go to Brooklyn",
                "expected": ["which", "Brooklyn", "where"],
            },
            {
                "query": "Coney Island",
                "expected": ["route", "train"],
            }
        ]
    )
    
    # ============================================================================
    # CATEGORY E: EDGE CASES & ERROR HANDLING
    # ============================================================================
    print(f"\n{Colors.BOLD}{Colors.HEADER}═══ CATEGORY E: EDGE CASES & ERROR HANDLING ═══{Colors.ENDC}")
    
    tester.run_test(
        "EDG-001",
        "Typo in station name",
        "How to get to Grand Centrall?",
        ["Grand Central", "route"],
        fail_keywords=["not found", "Could not"]
    )
    
    tester.run_test(
        "EDG-002",
        "Ambiguous Wall St (multiple stations)",
        "Next train at Wall St",
        ["Wall", "ambiguous", "which", "mean"]
    )
    
    tester.run_test(
        "EDG-003",
        "Non-subway query",
        "What's the weather today?",
        ["weather", "subway", "assist"],  # Should acknowledge but redirect
    )
    
    tester.run_test(
        "EDG-004",
        "Station with special characters",
        "From 42nd St & 8th Ave to Penn Station",
        ["route", "train"],
        fail_keywords=["not found"]
    )
    
    # ============================================================================
    # CATEGORY F: STATION NAME VARIATIONS
    # ============================================================================
    print(f"\n{Colors.BOLD}{Colors.HEADER}═══ CATEGORY F: STATION NAME VARIATIONS ═══{Colors.ENDC}")
    
    tester.run_test(
        "STA-001",
        "Abbreviation: GC for Grand Central",
        "I'm at GC",
        ["Grand Central"],
        fail_keywords=["not found", "Could not"]
    )
    
    tester.run_test(
        "STA-002",
        "Number variations",
        "Route from 42nd St to 34th St",
        ["route", "train", "42", "34"]
    )
    
    tester.run_test(
        "STA-003",
        "Flushing variations",
        "How to get to Flushing?",
        ["Flushing"],
        fail_keywords=["not found"]
    )
    
    # ============================================================================
    # PRINT SUMMARY AND EXPORT
    # ============================================================================
    tester.print_summary()
    tester.export_report("/Users/sj/Desktop/Capstone/Prototype/qa_test_results.json")

if __name__ == "__main__":
    main()
