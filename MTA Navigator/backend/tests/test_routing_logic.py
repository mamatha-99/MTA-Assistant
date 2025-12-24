import sys
import os
import networkx as nx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.services.graph_builder import GraphBuilder

def test_routes():
    print("Initializing Graph...")
    builder = GraphBuilder()
    G = builder.build()
    
    # Helper to print route
    def find_path(u, v, description):
        print(f"\n--- Testing: {description} ---")
        try:
            path = nx.shortest_path(G, source=u, target=v, weight='weight')
            total_time = 0
            for i in range(len(path)-1):
                p1 = path[i]
                p2 = path[i+1]
                edge = G[p1][p2]
                weight = edge['weight']
                routes = edge.get('routes', [])
                type_ = edge.get('type', '')
                
                # Check for Parent/Child Links (Weight 0)
                if weight == 0 and type_ == 'STATION_PATH':
                    continue
                    
                total_time += weight
                p1_name = G.nodes[p1]['name']
                p2_name = G.nodes[p2]['name']
                
                print(f"{p1_name} ({p1}) -> {p2_name} ({p2}) | Route: {routes} | Time: {weight}s")
                
            print(f"TOTAL ESTIMATED TIME: {total_time/60:.1f} min")
            
        except nx.NetworkXNoPath:
            print("❌ NO PATH FOUND!")
        except Exception as e:
            print(f"❌ ERROR: {e}")

    # Case 1: Simple Local Trip (1 Train)
    # 96 St (120S) -> 72 St (123S)
    find_path('120S', '123S', "Local Trip: 96 St -> 72 St (1 Line)")

    # Case 2: Express Trip (2/3 Train)
    # 96 St (120S) -> 72 St (120S is 1/2/3). 
    # Actually 96 St is '120'. 
    # Wait, in GTFS 1/2/3 share '120'.
    # Express should be faster.
    # Note: 120S -> 123S (Local stops at 86th? Yes 122S).
    # 2/3 Express goes 96 (120) -> 72 (123) directly? Or does 2/3 stop at 72?
    # Yes 2/3 stops at 96 and 72. Skips 86 (122), 79 (121).
    
    # Let's check 96 St to Times Sq (127S)
    find_path('120S', '127S', "Express vs Local: 96 St -> Times Sq (Should use 2/3)")

    # Case 3: Cross Town Transfer
    # Grand Central (631) -> Times Square (127) via Shuttle (GS) or 7.
    # We need to route from Parent to Parent ideally, but let's try Child IDs if we know them.
    # GC 7 Platform: 723S
    # Times Sq 7 Platform: 725S
    # This requires walking from 631S -> Parent -> 723S...
    # Let's try Parent ID routing if our finder supports it, but here we test raw graph.
    # We need to find the specific nodes for 7 Train.
    
    # Let's just try Generic Graph Search from GC (631) -> TSQ (Combined Complex?)
    # Times SQ has many parents? 127 is 1/2/3. 
    # Let's try 631 (GC Parent) -> 127 (TSQ Parent).
    # The edges Parent<->Child exist, so it should work.
    find_path('631', '127', "Transfer: Grand Central -> Times Sq")

    # Case 4: The Bronx -> Brooklyn (Long Haul)
    # Pelham Bay (601S) -> Brooklyn Bridge (420S)
    find_path('601S', '420S', "Long Haul: Pelham Bay -> Brooklyn Bridge")

if __name__ == "__main__":
    test_routes()
