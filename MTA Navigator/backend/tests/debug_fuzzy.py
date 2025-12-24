from fuzzywuzzy import process, fuzz
import pandas as pd
import os

STOPS_FILE = "gtfs_subway/stops.txt"

def debug_fuzzy():
    print("Loading stops...")
    df = pd.read_csv(STOPS_FILE)
    stops = df['stop_name'].unique().tolist()
    
    query = "82nd St"
    target = "82 St-Jackson Hts"
    
    print(f"\nComparing '{query}' vs '{target}':")
    print(f"Simple Ratio: {fuzz.ratio(query, target)}")
    print(f"Partial Ratio: {fuzz.partial_ratio(query, target)}")
    print(f"Token Sort Ratio: {fuzz.token_sort_ratio(query, target)}")
    print(f"Token Set Ratio: {fuzz.token_set_ratio(query, target)}")
    
    print("\nTop 5 results using default extract:")
    results = process.extract(query, stops, limit=5)
    for name, score in results:
        print(f"   {name}: {score}")

    print("\nTop 5 results using token_set_ratio:")
    results_set = process.extract(query, stops, limit=5, scorer=fuzz.token_set_ratio)
    for name, score in results_set:
        print(f"   {name}: {score}")

if __name__ == "__main__":
    debug_fuzzy()
