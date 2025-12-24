import sys
import os
import networkx as nx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.services.graph_builder import GraphBuilder

def test_routing_quality():
    print("=== ROUTING QUALITY AUDIT ===")
    
    # 1. Build Graph
    builder = GraphBuilder()
    G = builder.build()
    
    # 2. Test Cases (Scenarios where humans know the answer)
    
    scenarios = [
        {
            "name": "One Seat Ride vs Transfer",
            "origin": "631S", # Grand Central (4/5/6)
            "dest": "640S", # Brooklyn Bridge (4/5/6)
            # The 4/5 is 1 stop (Express). The 6 is many stops (Local).
            # But changing 4 -> 6 -> 4 should be penalized.
        },
        {
            "name": "Cross-Town Zig Zag",
            "origin": "A15", # 42 St - Port Authority
            "dest": "631", # Grand Central
            # Should take Shuttle (S) or 7.
            # Should NOT take A -> 1 -> 2 -> 5...
        }
    ]
    
    for sc in scenarios:
        print(f"\nScenario: {sc['name']}")
        o, d = sc['origin'], sc['dest']
        
        path = nx.shortest_path(G, source=o, target=d, weight='weight')
        cost = nx.shortest_path_length(G, source=o, target=d, weight='weight')
        
        print(f"Total Cost: {cost}s ({cost//60} min)")
        print("Path Segments:")
        
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            edge = G[u][v]
            
            w = edge['weight']
            etype = edge.get('type')
            routes = edge.get('routes', [])
            
            u_name = G.nodes[u].get('name', u)
            v_name = G.nodes[v].get('name', v)
            
            if etype == 'TRACK':
                print(f"  🚆 TRAIN ({', '.join(routes)}): {u_name} -> {v_name} ({w}s)")
            elif etype == 'TRANSFER':
                print(f"  🚶 TRANSFER: {u_name} -> {v_name} ({w}s)")
            elif etype == 'STATION_PATH':
                print(f"  📍 STATION: {u_name} -> {v_name} ({w}s)")

if __name__ == "__main__":
    test_routing_quality()
