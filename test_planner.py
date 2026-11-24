import json
import time

print("Loading precomputed databases...")
t0 = time.time()
with open(r'C:\Users\LENOVO\.gemini\antigravity\scratch\crowdedness-journey-planner\backend_data\routes_db.json', 'r', encoding='utf-8') as f:
    routes_db = json.load(f)
with open(r'C:\Users\LENOVO\.gemini\antigravity\scratch\crowdedness-journey-planner\backend_data\stops_db.json', 'r', encoding='utf-8') as f:
    stops_db = json.load(f)
print(f"Loaded {len(routes_db)} routes and {len(stops_db)} stops in {time.time()-t0:.3f}s")

def find_routes(origin_query, dest_query, hour=8, is_weekend=False, preference='balanced'):
    # Match origin and dest
    origin_matches = [s for s in stops_db if origin_query.lower() in s.lower()]
    dest_matches = [s for s in stops_db if dest_query.lower() in s.lower()]
    
    if not origin_matches or not dest_matches:
        return {'error': 'Stops not found'}
        
    orig_stop = origin_matches[0]
    dest_stop = dest_matches[0]
    
    print(f"\nPlanning journey: '{orig_stop}' -> '{dest_stop}' at {hour:02d}:00 (Weekend: {is_weekend}, Preference: {preference})")
    
    results = []
    
    # 1. Direct Routes
    for r_id, r_info in routes_db.items():
        stops = r_info['stops']
        if orig_stop in stops and dest_stop in stops:
            i_orig = stops.index(orig_stop)
            i_dest = stops.index(dest_stop)
            if i_orig < i_dest:
                n_stops = i_dest - i_orig
                est_time_mins = int(n_stops * 2.8 + 5)
                
                crowd_arr = r_info['hourly_crowdedness_weekend'] if is_weekend else r_info['hourly_crowdedness_weekday']
                base_crowd = crowd_arr[hour]
                
                # Segment crowd
                seg_factors = r_info.get('segment_load_factors', [1.0]*len(stops))
                trip_factors = seg_factors[i_orig:i_dest+1] if i_orig < len(seg_factors) else [1.0]
                avg_factor = sum(trip_factors) / max(1, len(trip_factors))
                trip_crowd = round(min(100.0, base_crowd * avg_factor), 1)
                
                # Seat probability
                if trip_crowd < 45:
                    seat_prob = 92
                    comfort_level = 'Seats Readily Available'
                    badge_color = 'green'
                elif trip_crowd < 70:
                    seat_prob = 65
                    comfort_level = 'Moderate / Some Seats'
                    badge_color = 'yellow'
                elif trip_crowd < 88:
                    seat_prob = 28
                    comfort_level = 'Standing Only'
                    badge_color = 'orange'
                else:
                    seat_prob = 8
                    comfort_level = 'Packed / Crush Load'
                    badge_color = 'red'
                    
                # Weights
                if preference == 'fastest':
                    score = est_time_mins * 0.75 + trip_crowd * 0.25
                elif preference == 'comfort':
                    score = est_time_mins * 0.25 + trip_crowd * 0.75
                else:
                    score = est_time_mins * 0.5 + trip_crowd * 0.5
                    
                results.append({
                    'type': 'direct',
                    'route_id': r_id,
                    'is_ac': r_info['is_ac'],
                    'stops_count': n_stops,
                    'est_time_mins': est_time_mins,
                    'crowdedness': trip_crowd,
                    'comfort_level': comfort_level,
                    'seat_prob': seat_prob,
                    'badge_color': badge_color,
                    'score': round(score, 1),
                    'total_tickets': r_info['total_tickets']
                })
                
    results.sort(key=lambda x: x['score'])
    return {
        'origin': orig_stop,
        'dest': dest_stop,
        'count': len(results),
        'options': results[:5]
    }

# Test sample queries
res1 = find_routes('Badarpur Border', 'Kapashera Border', hour=8, preference='balanced')
for opt in res1['options']:
    print(f"Option: Bus {opt['route_id']:8s} | Time: {opt['est_time_mins']}m | Crowd: {opt['crowdedness']}% ({opt['comfort_level']}) | Seat Prob: {opt['seat_prob']}% | AC: {opt['is_ac']}")

print("\n--- Compare with Midday 14:00 (Off-Peak) ---")
res2 = find_routes('Badarpur Border', 'Kapashera Border', hour=14, preference='balanced')
for opt in res2['options']:
    print(f"Option: Bus {opt['route_id']:8s} | Time: {opt['est_time_mins']}m | Crowd: {opt['crowdedness']}% ({opt['comfort_level']}) | Seat Prob: {opt['seat_prob']}% | AC: {opt['is_ac']}")
