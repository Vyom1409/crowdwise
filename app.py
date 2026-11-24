"""
Crowdedness-Aware Journey Planner — FastAPI Backend
Serves precomputed crowdedness estimates from 2.56M October 2026 Delhi bus tickets.
"""

import json
import os
import math
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "backend_data")

# ── Load precomputed databases ──────────────────────────────────────────────
print("Loading precomputed databases...")
with open(os.path.join(DATA_DIR, "routes_db.json"), "r", encoding="utf-8") as f:
    ROUTES_DB = json.load(f)
with open(os.path.join(DATA_DIR, "stops_db.json"), "r", encoding="utf-8") as f:
    STOPS_DB = json.load(f)
with open(os.path.join(DATA_DIR, "network_summary.json"), "r", encoding="utf-8") as f:
    NETWORK_SUMMARY = json.load(f)
with open(os.path.join(DATA_DIR, "spot_checks.json"), "r", encoding="utf-8") as f:
    SPOT_CHECKS = json.load(f)

# ── Load POI database ────────────────────────────────────────────────────────
POI_PATH = os.path.join(DATA_DIR, "poi_db.json")
POI_DB = {"metros": [], "cafes": [], "hospitals": []}
if os.path.exists(POI_PATH):
    with open(POI_PATH, "r", encoding="utf-8") as f:
        POI_DB = json.load(f)
    print(f"Loaded POI database: {len(POI_DB['metros'])} metros, {len(POI_DB['cafes'])} cafes, {len(POI_DB['hospitals'])} hospitals.")

def find_nearest_pois(lat: float, lon: float, max_items: int = 3):
    """Find nearest metros, cafes, and hospitals from a lat/lon point."""
    if not lat or not lon:
        return {"metros": [], "cafes": [], "hospitals": []}

    def score_list(items):
        scored = []
        for it in items:
            d_km = haversine_km(lat, lon, it["lat"], it["lon"])
            # walking minutes @ 4.8 km/h ~ 12.5 min/km
            walk_min = max(1, int(d_km * 12.5))
            entry = dict(it)
            entry["distance_km"] = round(d_km, 2)
            entry["distance_m"] = int(d_km * 1000)
            entry["walk_mins"] = walk_min
            scored.append(entry)
        scored.sort(key=lambda x: x["distance_km"])
        return scored[:max_items]

    return {
        "metros": score_list(POI_DB.get("metros", [])),
        "cafes": score_list(POI_DB.get("cafes", [])),
        "hospitals": score_list(POI_DB.get("hospitals", [])),
    }

def calculate_walking_stats(orig_coords, dest_coords, bus_dist_km=None):
    """Calculate walking distance, time, calories burnt, steps, and equivalents."""
    if orig_coords and dest_coords:
        direct_km = haversine_km(orig_coords[0], orig_coords[1], dest_coords[0], dest_coords[1])
        walk_dist_km = round(max(0.3, direct_km * 1.22), 2)
    elif bus_dist_km:
        walk_dist_km = round(max(0.3, bus_dist_km * 0.9), 2)
    else:
        walk_dist_km = 3.0

    walk_mins = max(2, int(walk_dist_km * 12.5))
    calories = int(walk_dist_km * 65) # ~65 kcal/km
    steps = int(walk_dist_km * 1330) # ~1330 steps/km
    co2_saved_kg = round(walk_dist_km * 0.12, 2) # ~120g/km saved

    # Food equivalent
    if calories < 90:
        food_eq = "1 cup Masala Chai ☕"
    elif calories < 180:
        food_eq = "1 plate Vegetable Cutlet 🥪"
    elif calories < 260:
        food_eq = "1 hot Samosa with Chutney 🥟"
    elif calories < 380:
        food_eq = "1 crispy Masala Dosa 🫓"
    elif calories < 500:
        food_eq = "1 plate Chole Bhature 🥘"
    else:
        food_eq = "1 full Thali Meal 🍛"

    return {
        "walk_dist_km": walk_dist_km,
        "walk_mins": walk_mins,
        "calories": calories,
        "steps": steps,
        "food_equivalent": food_eq,
        "co2_saved_kg": co2_saved_kg,
        "is_walkable_recommended": bool(walk_dist_km <= 2.5)
    }
# stop_name → list of route_ids that serve it
STOP_TO_ROUTES = {}
for r_id, r_info in ROUTES_DB.items():
    for s in r_info["stops"]:
        STOP_TO_ROUTES.setdefault(s, []).append(r_id)

# Normalized stop name index for fuzzy matching
STOP_NORM_INDEX = {}
for s_name in STOPS_DB:
    norm = s_name.strip().lower()
    STOP_NORM_INDEX[norm] = s_name
    # Also index without parenthetical suffixes
    paren_idx = norm.find("(")
    if paren_idx > 0:
        short = norm[:paren_idx].strip()
        if short not in STOP_NORM_INDEX:
            STOP_NORM_INDEX[short] = s_name

# Also add every route stop to index (some route stops might not be in STOPS_DB)
ALL_ROUTE_STOPS = set()
for r_info in ROUTES_DB.values():
    for s in r_info["stops"]:
        ALL_ROUTE_STOPS.add(s)
        norm = s.strip().lower()
        if norm not in STOP_NORM_INDEX:
            STOP_NORM_INDEX[norm] = s

print(f"Loaded {len(ROUTES_DB)} routes, {len(STOPS_DB)} stops, {len(STOP_NORM_INDEX)} index entries.")

# ── Helpers ─────────────────────────────────────────────────────────────────

def match_stop(query: str, limit: int = 10):
    """Fuzzy-match a stop name query against the index."""
    q = query.strip().lower()
    if not q:
        return []

    exact = STOP_NORM_INDEX.get(q)
    results = []
    if exact:
        results.append(exact)

    # Substring matches, scored by relevance
    scored = []
    for norm, canonical in STOP_NORM_INDEX.items():
        if canonical in results:
            continue
        if q in norm:
            # Score: shorter = more relevant, starts-with bonus
            bonus = 0 if norm.startswith(q) else 10
            scored.append((len(norm) + bonus, canonical))
        elif norm in q:
            scored.append((len(norm) + 20, canonical))

    scored.sort(key=lambda x: x[0])
    seen = set(results)
    for _, name in scored:
        if name not in seen:
            results.append(name)
            seen.add(name)
        if len(results) >= limit:
            break

    return results


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance between two lat/lon points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def crowd_label(pct):
    if pct < 40:
        return "low", "Seats Available", "#22c55e"
    elif pct < 65:
        return "moderate", "Some Seats", "#eab308"
    elif pct < 85:
        return "high", "Standing Only", "#f97316"
    else:
        return "very_high", "Packed / Crush", "#ef4444"


MAJOR_HUBS = [
    'Aiims', 'Dhaula Kuan', 'Nehru Place', 'Kashmere Gate Isbt', 'Central Secretariat',
    'Anand Vihar Isbt', 'Lajpat Nagar', 'Azadpur', 'Shahdara Terminal', 'Badarpur Border'
]

def plan_journey(origin: str, dest: str, hour: int = 9, is_weekend: bool = False, preference: str = "balanced"):
    """Find routes connecting origin to destination with crowdedness estimates."""
    origin_matches = match_stop(origin, limit=10)
    dest_matches = match_stop(dest, limit=10)

    if not origin_matches:
        return {"error": f"No stops found matching '{origin}'", "suggestions": []}
    if not dest_matches:
        return {"error": f"No stops found matching '{dest}'", "suggestions": []}

    results = []

    # 1. Try direct routes across candidate matched stops
    for orig_stop in origin_matches:
        for dest_stop in dest_matches:
            if orig_stop == dest_stop:
                continue

            orig_routes = set(STOP_TO_ROUTES.get(orig_stop, []))
            dest_routes = set(STOP_TO_ROUTES.get(dest_stop, []))
            common_routes = orig_routes & dest_routes

            for r_id in common_routes:
                r_info = ROUTES_DB[r_id]
                stops = r_info["stops"]

                try:
                    i_orig = stops.index(orig_stop)
                    i_dest = stops.index(dest_stop)
                except ValueError:
                    continue

                if i_orig >= i_dest:
                    continue

                n_stops = i_dest - i_orig
                est_time_mins = int(n_stops * 2.5 + 3)

                coords = r_info.get("coordinates", [])
                dist_km = 0.0
                if coords and len(coords) > i_dest:
                    for ci in range(i_orig, i_dest):
                        c1, c2 = coords[ci], coords[ci + 1]
                        if c1 and c2:
                            dist_km += haversine_km(c1[0], c1[1], c2[0], c2[1])
                dist_km = round(max(1.0, dist_km), 1)

                crowd_arr = r_info["hourly_crowdedness_weekend"] if is_weekend else r_info["hourly_crowdedness_weekday"]
                base_crowd = crowd_arr[hour] if 0 <= hour < 24 else crowd_arr[9]

                seg_factors = r_info.get("segment_load_factors", [1.0] * len(stops))
                trip_factors = seg_factors[i_orig:i_dest + 1] if i_orig < len(seg_factors) else [1.0]
                avg_factor = sum(trip_factors) / max(1, len(trip_factors))
                trip_crowd = round(min(100.0, base_crowd * avg_factor), 1)

                level, comfort_text, color = crowd_label(trip_crowd)

                if preference == "fastest":
                    score = est_time_mins * 0.8 + trip_crowd * 0.2
                elif preference == "comfort":
                    score = est_time_mins * 0.2 + trip_crowd * 0.8
                else:
                    score = est_time_mins * 0.5 + trip_crowd * 0.5

                fare = r_info.get("avg_fare", 15.0)

                path_coords = []
                if coords and len(coords) > i_dest:
                    for ci in range(i_orig, i_dest + 1):
                        if coords[ci]:
                            path_coords.append(coords[ci])

                results.append({
                    "type": "direct",
                    "route_id": r_id,
                    "route_name": r_info.get("route_name", r_id),
                    "direction": r_info.get("direction", ""),
                    "is_ac": r_info.get("is_ac", False),
                    "origin_stop": orig_stop,
                    "dest_stop": dest_stop,
                    "stops_count": n_stops,
                    "est_time_mins": est_time_mins,
                    "distance_km": dist_km,
                    "crowdedness_pct": trip_crowd,
                    "crowdedness_level": level,
                    "comfort_text": comfort_text,
                    "badge_color": color,
                    "fare_est": round(fare, 1),
                    "score": round(score, 1),
                    "total_route_tickets": r_info["total_tickets"],
                    "hourly_crowdedness": crowd_arr,
                    "path_coords": path_coords,
                })

    # 2. If few or no direct routes found, find 1-transfer routes via major hubs
    if len(results) < 2:
        for orig_stop in origin_matches[:3]:
            for dest_stop in dest_matches[:3]:
                for hub_name in MAJOR_HUBS:
                    hub_matches = match_stop(hub_name, limit=1)
                    if not hub_matches:
                        continue
                    hub_stop = hub_matches[0]
                    if hub_stop == orig_stop or hub_stop == dest_stop:
                        continue

                    # Leg 1: orig -> hub
                    r1_candidates = set(STOP_TO_ROUTES.get(orig_stop, [])) & set(STOP_TO_ROUTES.get(hub_stop, []))
                    # Leg 2: hub -> dest
                    r2_candidates = set(STOP_TO_ROUTES.get(hub_stop, [])) & set(STOP_TO_ROUTES.get(dest_stop, []))

                    if not r1_candidates or not r2_candidates:
                        continue

                    r1_id = list(r1_candidates)[0]
                    r2_id = list(r2_candidates)[0]
                    if r1_id == r2_id:
                        continue

                    r1_info = ROUTES_DB[r1_id]
                    r2_info = ROUTES_DB[r2_id]
                    s1 = r1_info["stops"]
                    s2 = r2_info["stops"]

                    try:
                        i_o1, i_h1 = s1.index(orig_stop), s1.index(hub_stop)
                        i_h2, i_d2 = s2.index(hub_stop), s2.index(dest_stop)
                    except ValueError:
                        continue

                    if i_o1 >= i_h1 or i_h2 >= i_d2:
                        continue

                    n_stops = (i_h1 - i_o1) + (i_d2 - i_h2)
                    est_time = int(n_stops * 2.5 + 10) # 10 min transfer

                    crowd1 = (r1_info["hourly_crowdedness_weekend"] if is_weekend else r1_info["hourly_crowdedness_weekday"])[hour]
                    crowd2 = (r2_info["hourly_crowdedness_weekend"] if is_weekend else r2_info["hourly_crowdedness_weekday"])[hour]
                    trip_crowd = round((crowd1 + crowd2) / 2.0, 1)

                    level, comfort_text, color = crowd_label(trip_crowd)
                    dist = round((r1_info.get("distance_km", 10) + r2_info.get("distance_km", 10)) * 0.6, 1)

                    # Build combined path coordinates
                    c1_list = r1_info.get("coordinates", [])[i_o1:i_h1+1]
                    c2_list = r2_info.get("coordinates", [])[i_h2:i_d2+1]
                    path_coords = [c for c in c1_list if c] + [c for c in c2_list if c]

                    results.append({
                        "type": "transfer",
                        "route_id": f"{r1_id} ➔ {r2_id}",
                        "route_name": f"{r1_id} ➔ {r2_id} (via {hub_stop})",
                        "direction": "1 Transfer",
                        "is_ac": r1_info.get("is_ac", False) or r2_info.get("is_ac", False),
                        "origin_stop": orig_stop,
                        "dest_stop": dest_stop,
                        "transfer_hub": hub_stop,
                        "stops_count": n_stops,
                        "est_time_mins": est_time,
                        "distance_km": dist,
                        "crowdedness_pct": trip_crowd,
                        "crowdedness_level": level,
                        "comfort_text": comfort_text,
                        "badge_color": color,
                        "fare_est": round(r1_info.get("avg_fare", 12) + r2_info.get("avg_fare", 12), 1),
                        "score": round(est_time * 0.5 + trip_crowd * 0.5 + 15, 1),
                        "total_route_tickets": r1_info["total_tickets"] + r2_info["total_tickets"],
                        "hourly_crowdedness": [(a + b)/2 for a, b in zip(r1_info["hourly_crowdedness_weekday"], r2_info["hourly_crowdedness_weekday"])],
                        "path_coords": path_coords,
                    })
                    break

    # Deduplicate by route_id (keep best score)
    seen = {}
    for r in results:
        key = r["route_id"]
        if key not in seen or r["score"] < seen[key]["score"]:
            seen[key] = r
    results = sorted(seen.values(), key=lambda x: x["score"])

    # Resolve coordinates for origin and destination
    orig_canonical = origin_matches[0]
    dest_canonical = dest_matches[0]
    orig_info = STOPS_DB.get(orig_canonical, {})
    dest_info = STOPS_DB.get(dest_canonical, {})
    orig_coords = [orig_info["lat"], orig_info["lon"]] if "lat" in orig_info else None
    dest_coords = [dest_info["lat"], dest_info["lon"]] if "lat" in dest_info else None

    # Calculate walking calories & health comparison
    bus_dist = results[0]["distance_km"] if results else None
    walking_stats = calculate_walking_stats(orig_coords, dest_coords, bus_dist)

    # Find nearest POIs (metros, cafes, hospitals) for origin and destination
    orig_pois = find_nearest_pois(orig_coords[0], orig_coords[1], max_items=3) if orig_coords else {"metros":[],"cafes":[],"hospitals":[]}
    dest_pois = find_nearest_pois(dest_coords[0], dest_coords[1], max_items=3) if dest_coords else {"metros":[],"cafes":[],"hospitals":[]}

    return {
        "origin": orig_canonical,
        "destination": dest_canonical,
        "origin_coords": orig_coords,
        "destination_coords": dest_coords,
        "hour": hour,
        "is_weekend": is_weekend,
        "preference": preference,
        "result_count": len(results),
        "options": results[:8],
        "walking_stats": walking_stats,
        "origin_pois": orig_pois,
        "destination_pois": dest_pois,
    }


# ── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(title="Delhi Bus Crowdedness Journey Planner", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = os.path.join(BASE_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/search-stops")
async def search_stops(q: str = Query("", min_length=1)):
    matches = match_stop(q, limit=12)
    results = []
    for m in matches:
        info = STOPS_DB.get(m, {})
        results.append({
            "name": m,
            "lat": info.get("lat"),
            "lon": info.get("lon"),
            "total_activity": info.get("total_activity", 0),
            "route_count": len(info.get("routes", [])),
        })
    return {"results": results}


@app.get("/api/plan")
async def api_plan(
    origin: str = Query(...),
    dest: str = Query(...),
    hour: int = Query(9, ge=0, le=23),
    weekend: bool = Query(False),
    preference: str = Query("balanced"),
):
    return plan_journey(origin, dest, hour, weekend, preference)


@app.get("/api/route/{route_id}")
async def get_route(route_id: str):
    r = ROUTES_DB.get(route_id)
    if not r:
        return {"error": "Route not found"}
    return r


@app.get("/api/stop/{stop_name}")
async def get_stop(stop_name: str):
    matches = match_stop(stop_name, limit=1)
    if not matches:
        return {"error": "Stop not found"}
    name = matches[0]
    info = STOPS_DB.get(name, {})
    routes_detail = []
    for r_id in info.get("routes", [])[:20]:
        r_info = ROUTES_DB.get(r_id)
        if r_info:
            routes_detail.append({
                "route_id": r_id,
                "is_ac": r_info.get("is_ac", False),
                "total_tickets": r_info["total_tickets"],
                "peak_hour": r_info["peak_hour"],
            })
    return {
        "stop_name": name,
        "lat": info.get("lat"),
        "lon": info.get("lon"),
        "boardings": info.get("boardings", 0),
        "alightings": info.get("alightings", 0),
        "routes": routes_detail,
    }


@app.get("/api/network-summary")
async def network_summary():
    return NETWORK_SUMMARY


@app.get("/api/spot-checks")
async def spot_checks():
    return SPOT_CHECKS


@app.get("/api/top-routes")
async def top_routes(limit: int = Query(20, ge=1, le=100)):
    sorted_routes = sorted(ROUTES_DB.values(), key=lambda r: r["total_tickets"], reverse=True)
    results = []
    for r in sorted_routes[:limit]:
        results.append({
            "route_id": r["route_id"],
            "total_tickets": r["total_tickets"],
            "total_passengers": r["total_passengers"],
            "is_ac": r.get("is_ac", False),
            "peak_hour": r["peak_hour"],
            "distance_km": r.get("distance_km", 0),
            "stops_count": len(r["stops"]),
            "peak_crowdedness": max(r["hourly_crowdedness_weekday"]),
        })
    return {"routes": results}


@app.get("/api/all-pois")
async def get_all_pois():
    """Return all POIs (metros, cafes, hospitals) for interactive map layers."""
    return POI_DB


@app.get("/api/nearby-poi")
async def get_nearby_poi(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(3, ge=1, le=10)
):
    """Find nearest metros, cafes, and hospitals from any lat/lon coordinate."""
    return find_nearest_pois(lat, lon, max_items=limit)


@app.get("/api/walking-calories")
async def get_walking_calories(
    distance_km: float = Query(..., gt=0),
    weight_kg: float = Query(68.0, gt=30, lt=200)
):
    """Calculate walking calories and food equivalent for any distance."""
    walk_mins = max(1, int(distance_km * 12.5))
    calories = int(distance_km * (weight_kg / 68.0) * 65)
    steps = int(distance_km * 1330)
    co2 = round(distance_km * 0.12, 2)
    return {
        "distance_km": distance_km,
        "walk_mins": walk_mins,
        "calories_burnt": calories,
        "steps": steps,
        "co2_saved_kg": co2
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
