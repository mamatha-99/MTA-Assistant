#!/usr/bin/env python3
"""
Quick script to identify all stations served by Green Line (4, 5, 6 trains)
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.data.database import SessionLocal, engine
import pandas as pd

# Check location_type values
query1 = """
SELECT DISTINCT location_type FROM stops
"""
print("Location types in database:")
df1 = pd.read_sql(query1, engine)
print(df1)

# Get all stops served by routes 4, 5, 6, 6X
query = """
SELECT DISTINCT s.stop_id, s.stop_name, s.location_type, s.parent_station
FROM stops s
JOIN stop_times st ON s.stop_id = st.stop_id
JOIN trips t ON st.trip_id = t.trip_id
WHERE t.route_id IN ('4', '5', '6', '6X')
ORDER BY s.stop_name
"""

print("\n" + "="*80)
print("GREEN LINE STATIONS (4, 5, 6 trains)")
print("="*80)

df = pd.read_sql(query, engine)
print(f"\nTotal stops (including platforms): {len(df)}")

# Show parent stations only (location_type might be string or int)
parents = df[(df['location_type'] == '1') | (df['location_type'] == 1)]
print(f"Parent stations (location_type='1'): {len(parents)}")

print("\nAll unique station names (first 20):")
unique_names = df['stop_name'].unique()
for name in sorted(unique_names)[:20]:
    print(f"  - {name}")

print(f"\n... and {len(unique_names) - 20} more stations")

# Get stations served by each route
for route in ['4', '5', '6']:
    route_query = f"""
    SELECT COUNT(DISTINCT s.stop_name) as count
    FROM stops s
    JOIN stop_times st ON s.stop_id = st.stop_id
    JOIN trips t ON st.trip_id = t.trip_id
    WHERE t.route_id = '{route}'
    """
    result = pd.read_sql(route_query, engine)
    print(f"\nRoute {route}: {result['count'].iloc[0]} unique stations")

# Save all stop IDs to file
all_stop_ids = df['stop_id'].tolist()
with open('/Users/sj/Desktop/Capstone/Green Line/green_line_stops.txt', 'w') as f:
    f.write(f"# GREEN LINE STOP IDS ({len(all_stop_ids)} total)\n")
    f.write("# Routes: 4, 5, 6, 6X (Lexington Avenue Line)\n")
    f.write("="*80 + "\n\n")
    for _, row in df.iterrows():
        f.write(f"{row['stop_id']}\t{row['stop_name']}\n")
    
print(f"\nSaved all green line stop IDs to green_line_stops.txt")

# Create a Python set for easy filtering
print(f"\nGREEN_LINE_STOP_IDS = {repr(set(all_stop_ids))}")
