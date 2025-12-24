# NYC Subway Assistant - Comprehensive QA Test Report
**Date:** December 12, 2025  
**Tester:** AI QA Agent  
**Version:** Prototype v1.0  

---

## 1. TEST OBJECTIVES

Rigorously test all system functionalities to ensure:
- ✅ Navigation/routing queries work correctly
- ✅ Train schedule queries return accurate real-time data
- ✅ Service alerts are properly retrieved and displayed
- ✅ Edge cases and ambiguous queries are handled gracefully
- ✅ Conversational context is maintained across multi-turn interactions
- ✅ Station name variations (colloquial, abbreviated) are correctly resolved

---

## 2. TEST ENVIRONMENT

- **Backend Server:** Running on http://localhost:8000
- **Database:** SQLite (subway.db)
- **Frontend:** HTML/CSS/JS interface
- **APIs:** OpenAI GPT-4, MTA Real-time Feeds

---

## 3. TEST CATEGORIES

### A. Navigation/Routing Tests
| Test ID | Description | User Query | Expected Outcome | Status |
|---------|-------------|------------|------------------|--------|
| NAV-001 | Basic route planning | "How do I get from Times Square to Grand Central?" | Valid route with train lines and transfers | ⏳ |
| NAV-002 | Route with transfer | "From Brooklyn Bridge to Central Park" | Multi-line route with transfer instructions | ⏳ |
| NAV-003 | Same line route | "From 34th St to 42nd St on the 6 train" | Direct route, no transfers | ⏳ |
| NAV-004 | Complex multi-transfer | "From Coney Island to Yankee Stadium" | Valid route with 2+ transfers | ⏳ |
| NAV-005 | Colloquial station names | "From GC to Penn Station" | Correctly interprets Grand Central and Penn Station | ⏳ |
| NAV-006 | Ambiguous station handling | "From 86th St to Union Square" | Asks for clarification on which 86th St | ⏳ |
| NAV-007 | Invalid station | "From Jupiter to Mars" | Graceful error message | ⏳ |
| NAV-008 | Missing destination | "I'm at Times Square" | Asks for destination | ⏳ |
| NAV-009 | Route duration display | "Fastest way from Wall St to Harlem" | Shows estimated travel time | ⏳ |
| NAV-010 | Reverse route | "How to get back from Flushing to Manhattan" | Valid return route | ⏳ |

### B. Train Schedule/Real-time Data Tests
| Test ID | Description | User Query | Expected Outcome | Status |
|---------|-------------|------------|------------------|--------|
| SCH-001 | Next train at station | "When is the next 7 train at Grand Central?" | List of upcoming arrivals with times | ⏳ |
| SCH-002 | Specific line query | "Show me Q train arrivals at Union Square" | Filtered arrivals for Q train only | ⏳ |
| SCH-003 | Station without real-time data | "Next train at [obscure station]" | Appropriate message if no data | ⏳ |
| SCH-004 | Multiple lines at station | "What trains are coming to 42nd St?" | Arrivals for all lines serving that station | ⏳ |
| SCH-005 | Time format validation | Check arrival times | Times shown in readable format (HH:MM and/or minutes) | ⏳ |

### C. Service Alert Tests
| Test ID | Description | User Query | Expected Outcome | Status |
|---------|-------------|------------|------------------|--------|
| ALE-001 | General alerts query | "Are there any service alerts?" | List of current system-wide alerts | ⏳ |
| ALE-002 | Line-specific alerts | "Any delays on the L train?" | Alerts filtered to L train | ⏳ |
| ALE-003 | Alerts in route planning | Get route from A to B | Alerts shown for lines in the route | ⏳ |
| ALE-004 | No alerts scenario | Query when no alerts exist | "No active alerts" message | ⏳ |

### D. Conversational Context Tests
| Test ID | Description | Conversation Flow | Expected Outcome | Status |
|---------|-------------|-------------------|------------------|--------|
| CTX-001 | Follow-up clarification | "86th St" → "Which one?" → "Lexington" | Uses context to resolve ambiguity | ⏳ |
| CTX-002 | Multi-turn planning | "I'm at Times Square" → "I want to go to Brooklyn" → "Which part?" → "Williamsburg" | Maintains origin across turns | ⏳ |
| CTX-003 | Session persistence | Ask multiple unrelated questions | Each gets appropriate response | ⏳ |
| CTX-004 | Context reset | Clear conversation, ask new question | Doesn't use old context inappropriately | ⏳ |

### E. Edge Cases & Error Handling
| Test ID | Description | User Query | Expected Outcome | Status |
|---------|-------------|------------|------------------|--------|
| EDG-001 | Typo in station name | "Grand Centrall" | Fuzzy matching corrects to Grand Central | ⏳ |
| EDG-002 | Partial station name | "Wall St" (multiple stations) | Lists disambiguation options | ⏳ |
| EDG-003 | Very long query | Complex multi-sentence request | Extracts intent correctly | ⏳ |
| EDG-004 | Empty message | "" | Appropriate error handling | ⏳ |
| EDG-005 | Non-subway query | "What's the weather?" | Responds but stays in scope | ⏳ |
| EDG-006 | Special characters | "From 42nd & 8th to Penn" | Handles special chars gracefully | ⏳ |

### F. Station Name Variations
| Test ID | Description | User Query | Expected Match | Status |
|---------|-------------|------------|----------------|--------|
| STA-001 | Abbreviations | "GC", "Grand Central" | Both resolve to same station | ⏳ |
| STA-002 | Number variations | "42nd St", "42 St", "Forty-Second St" | All resolve correctly | ⏳ |
| STA-003 | Borough references | "Flushing" vs "Flushing-Main St" | Correct station identified | ⏳ |
| STA-004 | Alternate names | "Herald Square" vs "34 St Herald Sq" | Same station | ⏳ |

---

## 4. TEST EXECUTION PLAN

1. **Phase 1:** Open frontend and verify UI loads
2. **Phase 2:** Execute Navigation tests (NAV-001 to NAV-010)
3. **Phase 3:** Execute Schedule tests (SCH-001 to SCH-005)
4. **Phase 4:** Execute Alert tests (ALE-001 to ALE-004)
5. **Phase 5:** Execute Context tests (CTX-001 to CTX-004)
6. **Phase 6:** Execute Edge case tests (EDG-001 to EDG-006)
7. **Phase 7:** Execute Station variation tests (STA-001 to STA-004)

---

## 5. TEST RESULTS

### Results will be populated during test execution

---

## 6. KNOWN ISSUES (from BUGS_AND_ISSUES.log)

- **Issue #1:** Fuzzy search quality - Some station matches return irrelevant results
- **Severity:** Medium
- **Impact:** UX friction when resolving ambiguous stations

---

## 7. CRITICAL BUGS FOUND

*To be populated during testing*

---

## 8. RECOMMENDATIONS

*To be populated after testing*

---

## 9. SIGN-OFF

- [ ] All critical tests passed
- [ ] All blocking bugs documented
- [ ] System ready for production / Next phase
