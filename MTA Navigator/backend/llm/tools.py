import sys
import os
import time
from datetime import datetime
import networkx as nx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.station_service import StationService
from backend.services.graph_builder import GraphBuilder
from backend.data.database import SessionLocal
from backend.data.realtime_schema import RealtimeUpdate, ServiceAlert

# ============================================================================
# GREEN LINE CONFIGURATION
# ============================================================================
# Only routes 4, 5, 6 (and express variant 6X) - Lexington Avenue Line
GREEN_LINE_ROUTES = ['4', '5', '6', '6X']
OUT_OF_SCOPE_MESSAGE = """I currently provide navigation assistance for the 4, 5, and 6 trains (Lexington Avenue Line - Green Line) only. 

We're working on expanding to cover the entire NYC subway system soon! 

Is there anything I can help you with regarding the 4, 5, or 6 trains?"""

# Global Service Instances (Lazy Loaded)
_graph = None
_station_service = None

def get_services():
    global _graph, _station_service
    if _graph is None:
        print("Loading Graph...")
        _graph = GraphBuilder().build()
    if _station_service is None:
        print("Loading Station Service...")
        _station_service = StationService()
    return _graph, _station_service

def get_nyc_direction(stop_id, from_name, to_name):
    """
    Returns proper NYC subway direction terminology instead of Northbound/Southbound.
    
    Uses authentic NYC subway terminology:
    - Manhattan: "Uptown" (north) / "Downtown" (south)
    - To Bronx: "Uptown to the Bronx" 
    - To Brooklyn: "Downtown to Brooklyn"
    - Within boroughs: Based on direction
    """
    # Determine if Northbound (N) or Southbound (S) from stop_id
    is_north = "N" in str(stop_id)
    is_south = "S" in str(stop_id)
    
    # Keywords to identify boroughs in station names
    bronx_keywords = ['Bronx', 'Woodlawn', 'Pelham', 'Parkchester', 'Hunts Point', 
                      'Yankee Stadium', 'Fordham', 'Bedford Park', 'Eastchester', 
                      'Nereid', 'Wakefield', 'Dyre']
    brooklyn_keywords = ['Brooklyn', 'Bergen', 'Crown', 'Franklin Av', 'Nostrand', 
                         'Kingston', 'Utica', 'Flatbush', 'New Lots', 'Nevins', 
                         'Atlantic Av', 'Barclays']
    
    # Check if destination is in Bronx or Brooklyn
    to_bronx = any(kw in to_name for kw in bronx_keywords)
    to_brooklyn = any(kw in to_name for kw in brooklyn_keywords)
    from_bronx = any(kw in from_name for kw in bronx_keywords)
    from_brooklyn = any(kw in from_name for kw in brooklyn_keywords)
    
    # Determine direction
    if to_brooklyn or (is_south and not from_bronx):
        return "Downtown to Brooklyn" if to_brooklyn else "Downtown"
    elif to_bronx or (is_north and not from_brooklyn):
        return "Uptown to the Bronx" if to_bronx else "Uptown"
    elif is_north:
        return "Uptown"
    elif is_south:
        return "Downtown"
    else:
        return ""


def resolve_station_ambiguity(query_str):
    """
    Resolves station query to stop IDs, handling ambiguity.
    
    Returns:
        tuple: (status, data)
            status: "TARGET_LIST" (single station/group) or "AMBIGUOUS" (multiple different stations)
            data: list of matching station dictionaries
    """
    _, station_svc = get_services()
    results = station_svc.search_stations(query_str, limit=10)
    
    if not results:
        return None, None
    
    # Prefer parent stations (location_type == '1')
    parents = [r for r in results if r['location_type'] == '1']
    candidates = parents if parents else results
    
    # Group by station name
    match_groups = {}
    top_score = candidates[0]['score']
    
    # Dynamic threshold: perfect match (100) vs high match (top - 10)
    threshold = top_score if top_score == 100 else (top_score - 10)
    
    for c in candidates:
        if c['score'] < threshold:
            continue
        name = c['match_name']
        if name not in match_groups:
            match_groups[name] = []
        match_groups[name].append(c)
    
    # CASE 1: Only ONE unique station name found
    # Even if there are multiple IDs (different platforms/entrances), treat as one station
    if len(match_groups) == 1:
        group_name = list(match_groups.keys())[0]
        station_list = match_groups[group_name]
        
        # If it's a single result, definitely not ambiguous
        if len(station_list) == 1:
            return "TARGET_LIST", station_list
        
        # Multiple IDs for same name - check if they're really the same station complex
        # (e.g., Wall St 230 and Wall St 419 are different complexes)
        # Look at the stop_id patterns - if very different, it's ambiguous
        stop_ids = [s['stop_id'] for s in station_list]
        
        # Check if these are likely the same complex by looking at proximity of IDs
        # If IDs are very different in number, might be different stations
        # For now, if we have multiple parents with same name, that's truly ambiguous
        if len(station_list) > 1 and all(s['location_type'] == '1' for s in station_list):
            # Multiple parent stations with same name = ambiguous (like Wall St 2/3 vs Wall St 4/5)
            return "AMBIGUOUS", station_list
        
        # Otherwise, return all as valid targets (multi-entrance same station)
        return "TARGET_LIST", station_list
    
    # CASE 2: Multiple different station NAMES - clearly ambiguous
    # e.g., "Union St" vs "Union Tpke" vs "14 St-Union Sq"
    flat_list = []
    for g in match_groups.values():
        flat_list.extend(g)
    
    return "AMBIGUOUS", flat_list

def tool_plan_trip(origin_query: str, dest_query: str):
    G, _ = get_services()
    
    # 1. Resolve to Potential Lists
    o_type, o_data = resolve_station_ambiguity(origin_query)
    d_type, d_data = resolve_station_ambiguity(dest_query)
    
    if not o_data: return f"Could not find origin '{origin_query}'."
    if not d_data: return f"Could not find destination '{dest_query}'."
    
    if o_type == "AMBIGUOUS":
        opts = ", ".join([f"{o['match_name']} ({o['stop_id']})" for o in o_data])
        return f"Ambiguous origin '{origin_query}'. Did you mean: {opts}?"
        
    if d_type == "AMBIGUOUS":
        opts = ", ".join([f"{d['match_name']} ({d['stop_id']})" for d in d_data])
        return f"Ambiguous destination '{dest_query}'. Did you mean: {opts}?"
        
    # Now we have lists of valid start points and end points
    # e.g. Origin=[GC], Dest=[Wall St 2/3, Wall St 4/5]
    
    best_path = None
    best_cost = float('inf')
    best_transfers = float('inf')
    
    # Try all pairs
    for origin in o_data:
        for dest in d_data:
            try:
                # We want shortest weighted path
                path = nx.shortest_path(G, source=origin['stop_id'], target=dest['stop_id'], weight='weight')
                cost = nx.path_weight(G, path, weight='weight')
                
                # Count transfers
                transfers = 0
                for i in range(len(path)-1):
                    if G[path[i]][path[i+1]].get('type') == 'TRANSFER':
                        transfers += 1
                        
                # Selection Logic:
                # Prefer Fewer Transfers significantly.
                # Since we added 120s penalty to transfers in graph build, 'cost' already reflects this somewhat.
                # But let's be explicit: If diff is small (< 5 mins), pick fewer transfers.
                
                # Compare to current best
                is_better = False
                if transfers < best_transfers:
                    is_better = True
                elif transfers == best_transfers and cost < best_cost:
                    is_better = True
                    
                if is_better:
                    best_path = path
                    best_cost = cost
                    best_transfers = transfers
                    best_origin_node = origin
                    best_dest_node = dest
                    
            except nx.NetworkXNoPath:
                continue
                
    if not best_path:
        return f"No route found between {origin_query} and {dest_query}."
        
    # Format Result using the Winner
    path = best_path
    
    # 3. Format Output
    steps = []
    total_time = 0
    first_leg_info = None
    
    current_leg = None
    used_routes = set()
    
    # Logic to collapse consecutive track segments
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edge = G[u][v]
        edge_type = edge.get('type', '')
        weight = edge['weight']
        routes = edge.get('routes', [])
        
        u_name = G.nodes[u].get('name', u)
        v_name = G.nodes[v].get('name', v)
        
        total_time += weight
        
        if weight == 0:
            continue
            
        if 'TRACK' in edge_type:
            # Update used routes
            for r in routes: used_routes.add(r)

            # Check if we can merge with previous leg
            if current_leg and current_leg['type'] == 'TRACK':
                common = set(current_leg['routes']).intersection(set(routes))
                if common:
                    # Merge
                    current_leg['routes'] = list(common)
                    current_leg['to_name'] = v_name
                    current_leg['duration'] += weight
                    current_leg['stops'].append(v_name)
                else:
                    # Different train line (e.g. Transfer or just change)
                    # Flush previous
                    _flush_leg(steps, current_leg)
                    
                    next_r = ", ".join(routes)
                    
                    # Fetch connection info
                    approx_arrival = time.time() + total_time
                    # note: total_time includes the current edge weight which we just added.
                    
                    # Assuming next_r routes are what we want.
                    # We need the stop ID where we are changing.
                    # current_leg['to_name'] is the name. We need the ID.
                    # The graph edge u->v. 'v' is the ID of the station we just arrived at.
                    # But wait, we might transfer to a sibling node?
                    # If this is a TRACK change (implicit transfer), 'v' is identifying the platform we are ON.
                    # So asking for next trains at 'v' for 'routes' is correct.
                    
                    conn_info = tool_get_next_trains(v, route_filter=routes, check_time=approx_arrival)
                    # Summarize connection (take first 2 lines)
                    conn_summary = ""
                    if "No live" not in conn_info and "No trains" not in conn_info:
                        lines = conn_info.split('\n')[:2]
                        conn_summary = " " + "; ".join(lines)
                    
                    steps.append(f"Change at {current_leg['to_name']} to {next_r} train.{conn_summary}")
                    
                    current_leg = None
            
            # Start new leg
            if not current_leg:
                # Determine Direction using proper NYC subway terminology
                direction = get_nyc_direction(u, u_name, v_name)
                
                current_leg = {
                    'type': 'TRACK',
                    'from_name': u_name,
                    'to_name': v_name,
                    'routes': routes,
                    'duration': weight,
                    'start_id': u,
                    'direction': direction,
                    'stops': [] # Intermediate stops
                }
                if not first_leg_info:
                    first_leg_info = {"stop_id": u, "routes": routes}
                    
        elif 'TRANSFER' in edge_type:
            if current_leg:
                _flush_leg(steps, current_leg)
                current_leg = None
            
            steps.append(f"Transfer at {u_name} -> {v_name} (~{weight}s)")
            
    # Flush final leg
    if current_leg:
        _flush_leg(steps, current_leg)

    summary = f"Route from {best_origin_node['match_name']} to {best_dest_node['match_name']}:\n"
    summary += f"Total Duration: {total_time // 60} min.\n"
    
    # Add Real-Time Arrival for First Leg
    if first_leg_info:
        rt_text = tool_get_next_trains(first_leg_info['stop_id'], route_filter=first_leg_info['routes'])
        summary += f"\nNEXT TRAIN ARRIVAL:\n{rt_text}\n"
        
    summary += "\nSTEPS:\n" + "\n".join(steps)
    
    # Add Alerts with detailed information
    if used_routes:
        alerts_summary = []
        for r in used_routes:
            alert = tool_get_alerts(r)
            if "No active" not in alert:
                # Format route name (6X -> 6 express)
                route_display = format_route_name(r)
                # Show full alert details
                alerts_summary.append(f"⚠️  {route_display} train: {alert}")
        
        if alerts_summary:
            summary += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            summary += "SERVICE ALERTS & DELAYS:\n"
            summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            summary += "\n".join(alerts_summary)
            summary += "\n\nPlease allow extra travel time for your journey."
        else:
            summary += "\n\n✓ No active alerts - Normal service on all your trains"
            
    return summary

def format_route_name(route):
    """
    Formats route name in authentic NYC style.
    6X -> 6 express
    4 -> 4
    """
    if route == '6X':
        return '6 express'
    return route

def get_terminal_station(direction, route):
    """
    Returns the terminal station for a given route and direction.
    This helps give directions like "Take the Uptown 6 train to Pelham Bay Park"
    """
    # Terminal stations for Green Line routes
    terminals = {
        '4': {
            'Uptown': 'Woodlawn',
            'Downtown': 'Crown Hts-Utica Av'
        },
        '5': {
            'Uptown to the Bronx': 'Eastchester-Dyre Av',
            'Uptown': 'Eastchester-Dyre Av',
            'Downtown to Brooklyn': 'Flatbush Av-Brooklyn College',
            'Downtown': 'Flatbush Av-Brooklyn College'
        },
        '6': {
            'Uptown': 'Pelham Bay Park',
            'Downtown': 'Brooklyn Bridge-City Hall'
        },
        '6X': {  # Express
            'Uptown': 'Pelham Bay Park',
            'Downtown': 'Brooklyn Bridge-City Hall'
        }
    }
    
    # Get terminal for this route and direction
    if route in terminals and direction in terminals[route]:
        return terminals[route][direction]
    
    # Fallback: try without "to the Bronx" or "to Brooklyn"
    if 'Bronx' in direction and route in terminals:
        return terminals[route].get('Uptown', '')
    elif 'Brooklyn' in direction and route in terminals:
        return terminals[route].get('Downtown', '')
    
    return ''

def _flush_leg(steps, leg):
    if leg['type'] == 'TRACK':
        routes = leg['routes']
        
        # Format route names (6X -> 6 express)
        formatted_routes = [format_route_name(r) for r in routes]
        r_str = ", ".join(formatted_routes)
        
        # Get terminal destination for primary route
        terminal = ''
        if routes and leg['direction']:
            terminal = get_terminal_station(leg['direction'], routes[0])
        
        # Simplified list of passing stations
        stops_str = ""
        if leg['stops']:
            count = len(leg['stops'])
            if count <= 5:
                names = ", ".join(leg['stops'])
                stops_str = f" (passing {names})"
            else:
                stops_str = f" ({count} stops)"
        
        # Build direction string with terminal
        dir_str = ""
        if leg['direction']:
            if terminal:
                dir_str = f" {leg['direction']} to {terminal}"
            else:
                dir_str = f" {leg['direction']}"
        
        steps.append(f"Take the {r_str} train{dir_str} from {leg['from_name']} to {leg['to_name']}{stops_str}. Duration: {leg['duration'] // 60} min.")
    else:
        # Generic/Walk
        steps.append(f"Move from {leg['from_name']} to {leg['to_name']} ({leg['duration']}s)")


def tool_get_next_trains(station_query: str, route_filter=None, check_time=None):
    """
    Gets the next incoming trains for a station.
    
    **GREEN LINE ONLY**: Only returns trains for routes 4, 5, 6, 6X
    """
    # If station_query is an ID (e.g. 631N), use it. Else resolve name.
    # Simple heuristic: if it looks like an ID, try directly?
    
    _, station_svc = get_services()
    # Check if it's likely an ID
    if any(char.isdigit() for char in station_query) and len(station_query) < 6:
        stop_id = station_query
    else:
        st_type, st_data = resolve_station_ambiguity(station_query)
        if not st_data: return f"Station '{station_query}' not found."
        
        if st_type == "AMBIGUOUS":
            opts = ", ".join([f"{o['match_name']} ({o['stop_id']})" for o in st_data])
            return f"Ambiguous station '{station_query}'. Did you mean: {opts}?"
            
        stop_id = st_data[0]['stop_id']
        
    # Query DB
    db = SessionLocal()
    try:
        now = check_time if check_time else time.time()
        
        # Hack: Search for stop_id LIKE '631%'
        query = db.query(RealtimeUpdate).filter(
            RealtimeUpdate.stop_id.like(f"{stop_id}%"),
            RealtimeUpdate.arrival_time > now,
            RealtimeUpdate.route_id.in_(GREEN_LINE_ROUTES)  # GREEN LINE FILTER
        ).order_by(RealtimeUpdate.arrival_time).limit(5)
        
        results = query.all()
        
        if not results:
            return "No live arrival data found for Green Line trains (4, 5, 6)."
            
        lines = []
        for r in results:
            if route_filter and r.route_id not in route_filter:
                continue
            t_str = datetime.fromtimestamp(r.arrival_time).strftime('%H:%M')
            wait = round((r.arrival_time - now)/60)
            lines.append(f"Route {r.route_id} at {t_str} ({wait} min)")
            
        return "\n".join(lines) if lines else "No trains matching filter."
        
    finally:
        db.close()


def tool_get_alerts(route_id=None):
    """
    Returns active service alerts with proper route ID display.
    
    **GREEN LINE ONLY**: Only returns alerts for routes 4, 5, 6, 6X
    
    Args:
        route_id: Optional route ID to filter alerts (e.g., "4", "5", "6")
    
    Returns:
        str: Formatted alert messages with route IDs
    """
    import json
    
    db = SessionLocal()
    try:
        query = db.query(ServiceAlert)
        alerts = query.all()
        
        if not alerts:
            return "No active service alerts for Green Line trains (4, 5, 6)."
        
        valid_alerts = []
        
        for alert in alerts:
            try:
                # Parse affected_entities
                entities_data = alert.affected_entities
                
                # Handle different data types
                if isinstance(entities_data, str):
                    # Try to parse as JSON
                    try:
                        entities_data = json.loads(entities_data)
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, treat as plain text (comma-separated or single value)
                        entities_data = entities_data.strip()
                
                # Extract route IDs
                route_ids = []
                
                if isinstance(entities_data, list):
                    # List of entities (could be dicts or strings)
                    for entity in entities_data:
                        if isinstance(entity, dict):
                            # Extract route_id from dict
                            if 'route_id' in entity:
                                route_ids.append(str(entity['route_id']))
                        elif isinstance(entity, str):
                            # Direct string value
                            route_ids.append(entity.strip())
                
                elif isinstance(entities_data, dict):
                    # Single entity dict
                    if 'route_id' in entities_data:
                        route_ids.append(str(entities_data['route_id']))
                
                elif isinstance(entities_data, str):
                    # Plain string - could be comma-separated
                    if entities_data:
                        # Split by comma and filter empty strings
                        route_ids = [r.strip() for r in entities_data.split(',') if r.strip()]
                
                # **GREEN LINE FILTER**: Only include alerts for Green Line routes
                green_line_routes_in_alert = [r for r in route_ids if r in GREEN_LINE_ROUTES]
                if not green_line_routes_in_alert and route_ids:
                    # This alert doesn't affect Green Line, skip it
                    continue
                
                # Format route string
                if green_line_routes_in_alert:
                    route_str = ", ".join(sorted(set(green_line_routes_in_alert)))
                else:
                    # No specific routes mentioned, might be system-wide
                    route_str = "System-wide"
                
                # Filter by specific route if requested
                if route_id:
                    if green_line_routes_in_alert and route_id not in green_line_routes_in_alert:
                        continue  # Skip this alert, doesn't affect requested route
                
                # Build alert message
                alert_msg = f"[{route_str}] {alert.header_text}"
                
                # Add description if available and not too long
                if hasattr(alert, 'description_text') and alert.description_text:
                    desc = alert.description_text.strip()
                    if desc and len(desc) < 150:
                        alert_msg += f" - {desc}"
                
                valid_alerts.append(alert_msg)
                
            except Exception as e:
                # Fallback for completely malformed data
                print(f"Warning: Could not parse alert {alert.alert_id}: {e}")
                continue
        
        if not valid_alerts:
            if route_id:
                return f"No active alerts for the {route_id} train."
            return "No active service alerts for Green Line trains (4, 5, 6)."
        
        # Return up to 10 most recent alerts
        return "\n".join(valid_alerts[:10])
        
    finally:
        db.close()
