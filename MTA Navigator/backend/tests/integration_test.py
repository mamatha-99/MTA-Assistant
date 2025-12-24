import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.station_service import StationService
from backend.services.graph_builder import GraphBuilder
from backend.data.database import SessionLocal
from backend.data.realtime_schema import RealtimeUpdate
import networkx as nx

def integration_test():
    print("=== STARTING INTEGRATION TEST ===")
    
    # 1. Initialize Services
    print("\n1. Initializing Services...")
    station_service = StationService()
    
    # We need to use the graph builder to get the graph, 
    # and ideally wrap it in a Routing logic class, but we can stick to raw nx for now logic check.
    # In Phase 2 we made `backend/services/routing.py` but then I rewrote the builder in `graph_builder.py`.
    # I should use the Logic from routing.py but inject the Robust Graph.
    
    # Let's just use GraphBuilder here to show the data flow
    builder = GraphBuilder()
    G = builder.build()
    
    # 2. Emulate User Request: "Grand Central to Wall St"
    origin_query = "Grand Central"
    dest_query = "Wall St"
    
    print(f"\n2. Resolving Stations for: '{origin_query}' -> '{dest_query}'")
    
    # Resolve Origin
    origins = station_service.search_stations(origin_query)
    if not origins:
        print("❌ Failed to resolve Origin")
        return
    origin_matches = [o for o in origins if o['location_type'] == '1'] # Prefer Parent
    if not origin_matches: origin_matches = origins 
    origin = origin_matches[0]
    print(f"   ✅ Selected Origin: {origin['match_name']} (ID: {origin['stop_id']})")

    # Resolve Dest
    dests = station_service.search_stations(dest_query)
    if not dests:
        print("❌ Failed to resolve Destination")
        return
    dest_matches = [d for d in dests if d['location_type'] == '1']
    if not dest_matches: dest_matches = dests
    dest = dest_matches[0]
    print(f"   ✅ Selected Destination: {dest['match_name']} (ID: {dest['stop_id']})")
    
    # 3. Routing
    print("\n3. Calculating Route...")
    try:
        path = nx.shortest_path(G, source=origin['stop_id'], target=dest['stop_id'], weight='weight')
        print(f"   ✅ Path found: {len(path)} nodes.")
    except nx.NetworkXNoPath:
        print("❌ No path found!")
        return

    # Extract first leg info for RealTime check
    # We need to find the first "Track" edge to know which Route to check
    first_route_id = None
    first_stop_child_id = None
    
    print("   --- Route Segments ---")
    for i in range(len(path)-1):
        u = path[i]
        v = path[i+1]
        edge = G[u][v]
        
        # Determine human readable info
        u_name = G.nodes[u].get('name', u)
        v_name = G.nodes[v].get('name', v)
        
        if edge['weight'] > 0:
            print(f"   -> {u_name} to {v_name} via {edge.get('routes')} ({edge['weight']}s)")
            
            # Capture the first real train leg
            if not first_route_id and 'TRACK' in edge.get('type', ''):
                first_route_id = edge['routes'][0] # Take first option
                first_stop_child_id = u # This is the platform we depart from?
                # Wait, u might be a Parent. Edge Parent->Child is Type=STATION_PATH.
                # If u is Parent, and v is Child, we are entering.
                # If u is Child, and v is Child (Track), that's the one.
                # Let's refine logic below.
        else:
            print(f"   (Transfer/Walk) {u_name} -> {v_name}")
            
    # Refine First Stop logic
    # Path usually: Parent -> Child (Entrance) -> Child (Next Station) ...
    # So path[1] should be the Child Platform ID of the origin.
    if len(path) > 1:
        first_platform_id = path[1]
        # And the edge path[1]->path[2] is the train ride.
        if len(path) > 2:
            routes = G[path[1]][path[2]].get('routes', [])
            if routes:
                first_route_id = routes[0]
                print(f"\n   🎯 Targeting Real-Time lookup for: Station {first_platform_id} ({G.nodes[first_platform_id]['name']}), Route {routes}")

    # 4. Real-Time Data Check
    print("\n4. Fetching Real-Time Stats...")
    
    if not first_platform_id:
        print("   ❌ Could not determine platform for lookup.")
        return

    db = SessionLocal()
    try:
        # Query for updates at this stop
        # We search by stop_id. Note GTFS-RT might use '631N' vs '631'.
        # Our graph node `first_platform_id` should match the RT `stop_id`.
        
        # Also, check current time to filter old ones
        now_ts = time.time()
        
        results = db.query(RealtimeUpdate).filter(
            RealtimeUpdate.stop_id == first_platform_id,
            RealtimeUpdate.arrival_time > now_ts
        ).order_by(RealtimeUpdate.arrival_time).limit(5).all()
        
        if results:
            print(f"   ✅ Found {len(results)} incoming trains using platform {first_platform_id}:")
            for r in results:
                # Format time
                arrival_dt = datetime.fromtimestamp(r.arrival_time).strftime('%H:%M:%S')
                mins_away = round((r.arrival_time - now_ts) / 60, 1)
                print(f"      - Route {r.route_id}: Arriving at {arrival_dt} ({mins_away} min away)")
                
                if str(r.route_id) == str(first_route_id):
                    print(f"        ✨ MATCH! This is the train recommended by the router.")
        else:
            print(f"   ⚠️ No live data found for {first_platform_id}. (Might be no service or feed gap)")
            # Fallback check: Look at ANY updates in DB to prove it's populated
            count = db.query(RealtimeUpdate).count()
            print(f"      (Debug: Total RT records in DB: {count})")
            
    finally:
        db.close()

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    integration_test()
