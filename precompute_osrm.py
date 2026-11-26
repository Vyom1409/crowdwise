"""
Precompute OSRM road geometry for the top Delhi bus corridors.
Primes backend/osrm_cache/ so during judging / demo the app has zero latency
and 100% offline resilience even if the public OSRM server is down.
"""

import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from osrm_service import get_road_route_sync, CACHE_DIR

DATA_DIR = os.path.join(BASE_DIR, "backend_data")
with open(os.path.join(DATA_DIR, "routes_db.json"), "r", encoding="utf-8") as f:
    routes_db = json.load(f)

# Top corridors from network_summary and spot_checks
priority_routes = [
    "717AUP", "717ADOWN", "511AUP", "729UP", "729DOWN",
    "511ADOWN", "623UP", "623DOWN", "578UP", "433DOWN", "544AUP"
]

print("=== Precomputing OSRM Road Geometries for Top Corridors ===")
print(f"Target Cache Directory: {CACHE_DIR}")

warmed = 0
for r_id in priority_routes:
    r_info = routes_db.get(r_id)
    if not r_info:
        continue
    coords = r_info.get("coordinates", [])
    valid = [c for c in coords if len(c) >= 2]
    if len(valid) >= 2:
        print(f"Caching route {r_id} ({len(valid)} stops)...", end="", flush=True)
        res = get_road_route_sync(valid)
        pts = len(res.get("road_geometry", []))
        is_cached = res.get("served_from_cache", False)
        print(f" -> {pts} road points (Cached: {is_cached}, {res.get('distance_km')} km)")
        warmed += 1

print(f"\nSuccessfully primed {warmed} priority routes into disk cache.")
print(f"Total cache files on disk: {len(os.listdir(CACHE_DIR))}")
