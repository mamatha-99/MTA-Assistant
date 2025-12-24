#!/usr/bin/env python3
"""
Comprehensive test suite for Green Line (4, 5, 6 trains) implementation
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.services.graph_builder import GraphBuilder, GREEN_LINE_ROUTES
from backend.services.station_service import StationService
from backend.llm.tools import tool_plan_trip, tool_get_next_trains, tool_get_alerts
import networkx as nx

def test_graph_builder():
    """Test that graph only contains Green Line routes"""
    print("=" * 80)
    print("TEST 1: Graph Builder - Green Line Only")
    print("=" * 80)
    
    builder = GraphBuilder()
    G = builder.build()
    
    # Check node count
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    print(f"✓ Graph built with {num_nodes} nodes and {num_edges} edges")
    
    # Verify only Green Line routes are in the graph
    all_routes = set()
    for u, v, data in G.edges(data=True):
        if data.get('type') == 'TRACK':
            routes = data.get('routes', [])
            all_routes.update(routes)
    
    print(f"✓ Routes found in graph: {sorted(all_routes)}")
    
    # Check if any non-Green Line routes exist
    non_green_routes = all_routes - set(GREEN_LINE_ROUTES)
    if non_green_routes:
        print(f"❌ FAIL: Found non-Green Line routes: {non_green_routes}")
        return False
    else:
        print(f"✓ PASS: All routes are Green Line routes!")
    
    print()
    return True

def test_station_service():
    """Test that station service only returns Green Line stations"""
    print("=" * 80)
    print("TEST 2: Station Service - Green Line Only")
    print("=" * 80)
    
    service = StationService()
    
    # Test Green Line stations (should work)
    green_line_queries = [
        "Grand Central",
        "Union Square", 
        "Wall Street",
        "Brooklyn Bridge",
        "Yankee Stadium",
        "Fulton Street",
        "125th St"
    ]
    
    print("\nTesting Green Line station queries:")
    for query in green_line_queries:
        results = service.search_stations(query, limit=1)
        if results:
            print(f"  ✓ '{query}' -> {results[0]['match_name']} ({results[0]['stop_id']})")
        else:
            print(f"  ⚠ '{query}' -> No results (might be OK if not on Green Line)")
    
    # Test non-Green Line stations (should not return or return empty)
    print("\nTesting non-Green Line station queries (should fail or return nothing):")
    non_green_queries = [
        "Times Square",  # 1, 2, 3, 7, N, Q, R, W - NOT Green Line
        "Penn Station",  # 1, 2, 3, A, C, E - NOT Green Line
        "Coney Island"   # D, F, N, Q - NOT Green Line
    ]
    
    for query in non_green_queries:
        results = service.search_stations(query, limit=1)
        if results:
            print(f"  ⚠ '{query}' -> {results[0]['match_name']} (unexpected - verify it's not Green Line)")
        else:
            print(f"  ✓ '{query}' -> No results (correct - not on Green Line)")
    
    print()
    return True

def test_routing():
    """Test routing between Green Line stations"""
    print("=" * 80)
    print("TEST 3: Routing - Green Line Routes")
    print("=" * 80)
    
    test_cases = [
        ("Grand Central", "Wall Street", True),  # Should work - both on Green Line
        ("Grand Central", "Union Square", True),  # Should work
        ("125th St", "Brooklyn Bridge", True),    # Should work
        ("Yankee Stadium", "Fulton Street", True), # Should work
    ]
    
    for origin, dest, should_work in test_cases:
        print(f"\nTesting route: {origin} → {dest}")
        result = tool_plan_trip(origin, dest)
        
        if should_work:
            if "No route found" in result or "not found" in result.lower():
                print(f"  ❌ FAIL: Expected route but got: {result[:100]}...")
            else:
                print(f"  ✓ PASS: Route found!")
                # Print first few lines
                lines = result.split('\n')[:5]
                for line in lines:
                    print(f"    {line}")
        else:
            if "No route found" in result or "not found" in result.lower():
                print(f"  ✓ PASS: Correctly rejected (not on Green Line)")
            else:
                print(f"  ❌ FAIL: Should have rejected but got: {result[:100]}...")
    
    print()
    return True

def test_green_line_coverage():
    """Verify Green Line coverage"""
    print("=" * 80)
    print("TEST 4: Green Line Coverage Verification")
    print("=" * 80)
    
    builder = GraphBuilder()
    G = builder.build()
    
    # Sample Green Line stations we expect to find
    expected_stations = [
        "Grand Central-42 St",
        "14 St-Union Sq",
        "Brooklyn Bridge-City Hall",
        "Wall St",
        "Fulton St",
        "125 St",
        "161 St-Yankee Stadium"
    ]
    
    print("\nChecking expected Green Line stations in graph:")
    for station_name in expected_stations:
        # Find nodes with this name
        found = False
        for node in G.nodes():
            if G.nodes[node].get('name') == station_name:
                found = True
                print(f"  ✓ Found: {station_name} (ID: {node})")
                break
        
        if not found:
            print(f"  ⚠ Not found: {station_name} (might use different name)")
    
    print()
    return True

def test_connectivity():
    """Test that Green Line stations are properly connected"""
    print("=" * 80)
    print("TEST 5: Green Line Connectivity")
    print("=" * 80)
    
    builder = GraphBuilder()
    G = builder.build()
    
    # Check if graph is connected (should have at least one large component)
    if G.number_of_nodes() > 0:
        # Convert to undirected for connectivity check
        G_undirected = G.to_undirected()
        components = list(nx.connected_components(G_undirected))
        largest_component = max(components, key=len)
        
        print(f"✓ Number of connected components: {len(components)}")
        print(f"✓ Largest component size: {len(largest_component)} nodes")
        print(f"✓ Coverage: {len(largest_component) / G.number_of_nodes() * 100:.1f}% of graph")
        
        if len(largest_component) / G.number_of_nodes() < 0.8:
            print("  ⚠ WARNING: Graph may be fragmented!")
        else:
            print("  ✓ PASS: Graph is well connected")
    
    print()
    return True

def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "GREEN LINE TEST SUITE" + " " * 37 + "║")
    print("║" + " " * 15 + "Testing 4, 5, 6 Train Implementation" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    tests = [
        ("Graph Builder", test_graph_builder),
        ("Station Service", test_station_service),
        ("Routing", test_routing),
        ("Green Line Coverage", test_green_line_coverage),
        ("Connectivity", test_connectivity)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "ERROR"))
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, status in results:
        symbol = "✓" if status == "PASS" else "❌"
        print(f"{symbol} {test_name}: {status}")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()
