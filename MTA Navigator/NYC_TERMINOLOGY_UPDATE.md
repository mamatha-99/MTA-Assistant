# NYC Subway Terminology Update - Authentic Language

## Changes Implemented

Successfully updated the chatbot to use **authentic NYC subway terminology** instead of generic transit language.

## What Changed

### 1. Direction Terminology
**Before:** Northbound/Southbound (generic)
**After:** Uptown/Downtown (authentic NYC)

| Old Term | New Term | When Used |
|----------|----------|-----------|
| Northbound | Uptown | Manhattan heading north |
| Southbound | Downtown | Manhattan heading south |
| Northbound | Uptown to the Bronx | From Manhattan to Bronx |
| Southbound | Downtown to Brooklyn | From Manhattan to Brooklyn |

### 2. Train References
**Before:** "route 4", "line 5", "4 line"
**After:** "4 train", "5 train", "6 train"

This matches how New Yorkers actually talk about the subway.

### 3. Code Changes

**File: `backend/llm/tools.py`**
- Added `get_nyc_direction()` function to intelligently determine directions
- Logic considers:
  - Station direction (N/S in stop_id)
  - Destination borough (Brooklyn, Bronx keywords)
  - Origin borough
  - Returns authentic terminology

**File: `backend/api/main.py`**
- Added NYC Terminology section to system prompt
- Examples of correct phrasing for the LLM
- Instructions to use "train" not "route" or "line"

## Examples

### Example 1: Zerega Av → 33rd St
**Response:**
```
1. Take the 6X train Downtown from Zerega Av to 125 St
   Duration: 17 minutes

2. Change at 125 St to the 4 or 5 train

3. Take the 4 train Downtown from 125 St to 33 St
   Duration: 12 minutes
```

✓ Uses "6X train", "4 train" (not "route" or "line")
✓ Uses "Downtown" (not "Southbound")

### Example 2: Grand Central → Brooklyn Bridge
**Response:**
```
1. Board the 5 train Downtown at Grand Central-42 St
2. Exit at Brooklyn Bridge-City Hall

Total Duration: Approximately 8 minutes
```

✓ Uses "5 train"
✓ Uses "Downtown"

### Example 3: Yankee Stadium → Wall Street
**Response:**
```
1. Board the 4 train Downtown at 161 St-Yankee Stadium
2. Exit at Wall St

Total Duration: Approximately 28 minutes
```

✓ Uses "4 train"
✓ Uses "Downtown" (from Bronx to Manhattan)

## Direction Logic

The `get_nyc_direction()` function handles various scenarios:

```python
# Manhattan to Brooklyn
"Downtown to Brooklyn"

# Manhattan to Bronx  
"Uptown to the Bronx"

# Within Manhattan going north
"Uptown"

# Within Manhattan going south
"Downtown"

# Within Bronx/Brooklyn
Uses appropriate directional term based on context
```

## Benefits

✅ **Authentic NYC Language**: Matches how real New Yorkers talk
✅ **Better User Experience**: Familiar terminology for locals and tourists
✅ **Professional**: Sounds like official MTA communications
✅ **Clear Directions**: Easier to understand than generic "Northbound/Southbound"

## Testing

All test queries now return authentic NYC terminology:

```bash
✓ "How do I get from Zerega Av to 33rd St?"
  → Uses "Downtown", "4 train", "6X train"

✓ "Take me from Grand Central to Brooklyn Bridge"
  → Uses "Downtown", "5 train"

✓ "Yankee Stadium to Wall Street"
  → Uses "Downtown", "4 train"
```

## Compatibility

The changes are:
- ✅ Backward compatible (old queries still work)
- ✅ Works with all Green Line routes (4, 5, 6, 6X)
- ✅ Integrated with GPT-4o-mini cost optimization
- ✅ No impact on routing logic (only presentation)

## Status

**✅ Production Ready** with authentic NYC subway terminology!

New Yorkers will immediately recognize this as proper subway language, and tourists will get clearer, more authentic directions.
