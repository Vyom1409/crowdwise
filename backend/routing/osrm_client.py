"""
OSRM Road & Pedestrian Routing Client
Integrates OpenStreetMap / OSRM routing service with deterministic SHA-256 disk cache,
waypoint chunking, retry with exponential backoff, table distance matrix, and graceful fallback.
"""

import os
import json
import hashlib
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import httpx

# Determine repository root and cache directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# If in backend/routing, go up to backend
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
CACHE_DIR = os.path.join(BACKEND_DIR, "osrm_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Base URL configured via environment variable with fallback to public demo server
DEFAULT_OSRM_URL = "http://router.project-osrm.org"
OSRM_BASE_URL = os.environ.get("OSRM_BASE_URL", DEFAULT_OSRM_URL).rstrip("/")

MAX_WAYPOINTS_PER_CHUNK = 18
DEFAULT_TIMEOUT_SEC = 5.0
MAX_RETRIES = 2
BACKOFF_BASE_SEC = 0.5
USER_AGENT = "CrowdWise-Delhi/2.0 (hackathon-transit-routing)"

# Telemetry for benchmarks
_CACHE_STATS = {
    "hits": 0,
    "misses": 0,
    "last_rtt_ms": 0.0,
}


def _coords_to_cache_key(coords: List[List[float]], profile: str = "driving") -> str:
    """Generate deterministic SHA-256 cache key from exact coordinates, order, and profile."""
    repr_str = f"{profile}:" + ";".join(
        f"{float(c[0]):.5f},{float(c[1]):.5f}" for c in coords if len(c) >= 2 and c[0] is not None and c[1] is not None
    )
    return hashlib.sha256(repr_str.encode("utf-8")).hexdigest()


def _get_cache_path(cache_key: str) -> str:
    return os.path.join(CACHE_DIR, f"{cache_key}.json")


def _read_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    path = _get_cache_path(cache_key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data and isinstance(data, dict) and data.get("code") == "Ok" and "routes" in data:
                return data
    except Exception:
        pass
    return None


def _write_to_cache_atomic(cache_key: str, data: Dict[str, Any]) -> None:
    """Write valid response atomically to disk cache (temp file -> atomic rename)."""
    if not data or data.get("code") != "Ok" or not data.get("routes"):
        return

    final_path = _get_cache_path(cache_key)
    tmp_path = os.path.join(CACHE_DIR, f"{cache_key}_{os.getpid()}_{time.time_ns()}.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_path, final_path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _chunk_coords(coords: List[List[float]], max_chunk: int = MAX_WAYPOINTS_PER_CHUNK) -> List[List[List[float]]]:
    """Split coordinates into chunks with 1 contiguous overlapping waypoint."""
    if len(coords) <= max_chunk:
        return [coords]

    chunks = []
    i = 0
    while i < len(coords):
        chunk = coords[i : i + max_chunk]
        if len(chunk) < 2:
            break
        chunks.append(chunk)
        i += (max_chunk - 1)
    return chunks


async def _fetch_osrm_chunk_async(
    client: httpx.AsyncClient, chunk: List[List[float]], profile: str = "driving"
) -> Optional[Dict[str, Any]]:
    """Fetch road/walk route for a single chunk with retry, backoff, and caching."""
    cache_key = _coords_to_cache_key(chunk, profile)
    cached = _read_from_cache(cache_key)
    if cached:
        _CACHE_STATS["hits"] += 1
        cached["_from_cache"] = True
        return cached

    _CACHE_STATS["misses"] += 1
    # OSRM format: /route/v1/{profile}/{lng1},{lat1};{lng2},{lat2}...?overview=full&geometries=geojson
    coord_param = ";".join(f"{c[1]:.5f},{c[0]:.5f}" for c in chunk)
    url = f"{OSRM_BASE_URL}/route/v1/{profile}/{coord_param}?overview=full&geometries=geojson"
    headers = {"User-Agent": USER_AGENT}

    t0 = time.perf_counter()
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT_SEC)
            _CACHE_STATS["last_rtt_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    _write_to_cache_atomic(cache_key, data)
                    data["_from_cache"] = False
                    return data
            elif resp.status_code == 429:
                await asyncio.sleep(BACKOFF_BASE_SEC * (2**attempt))
            else:
                break
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt < MAX_RETRIES:
                await asyncio.sleep(BACKOFF_BASE_SEC * (2**attempt))

    return None


def _fetch_osrm_chunk_sync(chunk: List[List[float]], profile: str = "driving") -> Optional[Dict[str, Any]]:
    """Synchronous fetch for scripts and background tools."""
    cache_key = _coords_to_cache_key(chunk, profile)
    cached = _read_from_cache(cache_key)
    if cached:
        _CACHE_STATS["hits"] += 1
        cached["_from_cache"] = True
        return cached

    _CACHE_STATS["misses"] += 1
    coord_param = ";".join(f"{c[1]:.5f},{c[0]:.5f}" for c in chunk)
    url = f"{OSRM_BASE_URL}/route/v1/{profile}/{coord_param}?overview=full&geometries=geojson"
    headers = {"User-Agent": USER_AGENT}

    t0 = time.perf_counter()
    with httpx.Client(timeout=DEFAULT_TIMEOUT_SEC) as client:
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = client.get(url, headers=headers)
                _CACHE_STATS["last_rtt_ms"] = round((time.perf_counter() - t0) * 1000, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        _write_to_cache_atomic(cache_key, data)
                        data["_from_cache"] = False
                        return data
                elif resp.status_code == 429:
                    time.sleep(BACKOFF_BASE_SEC * (2**attempt))
                else:
                    break
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE_SEC * (2**attempt))

    return None


async def get_road_route_async(
    coords: List[List[float]],
    profile: str = "driving",
    fallback_dist_km: float = 0.0,
    fallback_mins: int = 0,
) -> Dict[str, Any]:
    """
    Given an ordered list of [lat, lon] coordinates, returns road-following geometry,
    accurate distance (km), duration (mins), and approximate fallback flags.
    Coordinates in road_geometry are returned in [lat, lon] order ready for Leaflet.
    """
    valid_coords = [
        c
        for c in coords
        if isinstance(c, (list, tuple)) and len(c) >= 2 and c[0] is not None and c[1] is not None
    ]
    if len(valid_coords) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": round(fallback_dist_km, 1),
            "duration_mins": int(fallback_mins),
            "is_approximate": True,
            "fallback_reason": "Insufficient coordinates (less than 2 waypoints)",
            "served_from_cache": False,
        }

    chunks = _chunk_coords(valid_coords, MAX_WAYPOINTS_PER_CHUNK)
    merged_geometry: List[List[float]] = []
    total_dist_meters = 0.0
    total_dur_seconds = 0.0
    all_from_cache = True
    any_chunk_failed = False

    async with httpx.AsyncClient() as client:
        for chunk in chunks:
            chunk_data = await _fetch_osrm_chunk_async(client, chunk, profile)
            if not chunk_data or not chunk_data.get("routes"):
                any_chunk_failed = True
                break

            if not chunk_data.get("_from_cache", False):
                all_from_cache = False

            route = chunk_data["routes"][0]
            total_dist_meters += route.get("distance", 0.0)
            total_dur_seconds += route.get("duration", 0.0)

            # Flip OSRM GeoJSON [lon, lat] -> Leaflet [lat, lon]
            geom = route.get("geometry", {})
            raw_pts = geom.get("coordinates", [])
            for pt in raw_pts:
                lat_lon = [round(pt[1], 5), round(pt[0], 5)]
                # Deduplicate consecutive boundary junction coordinates
                if not merged_geometry or merged_geometry[-1] != lat_lon:
                    merged_geometry.append(lat_lon)

    if any_chunk_failed or len(merged_geometry) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": round(fallback_dist_km, 1),
            "duration_mins": int(fallback_mins),
            "is_approximate": True,
            "fallback_reason": "OSRM routing unavailable; displaying straight line",
            "served_from_cache": False,
        }

    dist_km = round(total_dist_meters / 1000.0, 1)
    dur_mins = max(1, int(round(total_dur_seconds / 60.0)))

    return {
        "road_geometry": merged_geometry,
        "distance_km": dist_km,
        "duration_mins": dur_mins,
        "is_approximate": False,
        "fallback_reason": None,
        "served_from_cache": all_from_cache,
    }


def get_road_route_sync(
    coords: List[List[float]],
    profile: str = "driving",
    fallback_dist_km: float = 0.0,
    fallback_mins: int = 0,
) -> Dict[str, Any]:
    """Synchronous version of get_road_route for offline seeding and CLI scripts."""
    valid_coords = [
        c
        for c in coords
        if isinstance(c, (list, tuple)) and len(c) >= 2 and c[0] is not None and c[1] is not None
    ]
    if len(valid_coords) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": round(fallback_dist_km, 1),
            "duration_mins": int(fallback_mins),
            "is_approximate": True,
            "fallback_reason": "Insufficient coordinates (less than 2 waypoints)",
            "served_from_cache": False,
        }

    chunks = _chunk_coords(valid_coords, MAX_WAYPOINTS_PER_CHUNK)
    merged_geometry: List[List[float]] = []
    total_dist_meters = 0.0
    total_dur_seconds = 0.0
    all_from_cache = True
    any_chunk_failed = False

    for chunk in chunks:
        chunk_data = _fetch_osrm_chunk_sync(chunk, profile)
        if not chunk_data or not chunk_data.get("routes"):
            any_chunk_failed = True
            break

        if not chunk_data.get("_from_cache", False):
            all_from_cache = False

        route = chunk_data["routes"][0]
        total_dist_meters += route.get("distance", 0.0)
        total_dur_seconds += route.get("duration", 0.0)

        geom = route.get("geometry", {})
        raw_pts = geom.get("coordinates", [])
        for pt in raw_pts:
            lat_lon = [round(pt[1], 5), round(pt[0], 5)]
            if not merged_geometry or merged_geometry[-1] != lat_lon:
                merged_geometry.append(lat_lon)

    if any_chunk_failed or len(merged_geometry) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": round(fallback_dist_km, 1),
            "duration_mins": int(fallback_mins),
            "is_approximate": True,
            "fallback_reason": "OSRM routing unavailable; displaying straight line",
            "served_from_cache": False,
        }

    return {
        "road_geometry": merged_geometry,
        "distance_km": round(total_dist_meters / 1000.0, 1),
        "duration_mins": max(1, int(round(total_dur_seconds / 60.0))),
        "is_approximate": False,
        "fallback_reason": None,
        "served_from_cache": all_from_cache,
    }


async def get_table_async(
    sources: List[List[float]],
    destinations: List[List[float]],
    profile: str = "driving",
) -> Optional[List[List[float]]]:
    """
    Query OSRM /table/v1/{profile} to get duration matrix (in minutes) between sources and destinations.
    Coordinates are [lat, lon]. Returns None on failure so caller can fallback to Haversine.
    """
    if not sources or not destinations:
        return None

    # OSRM table takes a list of all coordinates, and parameters sources=0;1;... destinations=...
    all_coords = sources + destinations
    src_indices = ";".join(str(i) for i in range(len(sources)))
    dst_indices = ";".join(str(len(sources) + j) for j in range(len(destinations)))

    coord_str = ";".join(f"{c[1]:.5f},{c[0]:.5f}" for c in all_coords)
    url = f"{OSRM_BASE_URL}/table/v1/{profile}/{coord_str}?sources={src_indices}&destinations={dst_indices}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT_SEC)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and "durations" in data:
                    # Durations in seconds -> convert to minutes
                    return [[round((d or 0) / 60.0, 1) for d in row] for row in data["durations"]]
    except Exception:
        pass
    return None


def get_cache_stats() -> Dict[str, Any]:
    """Returns disk cache usage and query statistics."""
    cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    total_bytes = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in cache_files)
    total_queries = _CACHE_STATS["hits"] + _CACHE_STATS["misses"]
    hit_rate = round((_CACHE_STATS["hits"] / total_queries * 100.0), 1) if total_queries > 0 else 100.0

    return {
        "cached_corridors_count": len(cache_files),
        "total_cache_size_kb": round(total_bytes / 1024, 1),
        "cache_hits": _CACHE_STATS["hits"],
        "cache_misses": _CACHE_STATS["misses"],
        "hit_rate_pct": hit_rate,
        "last_rtt_ms": _CACHE_STATS["last_rtt_ms"],
        "osrm_endpoint": OSRM_BASE_URL,
    }


def clear_cache() -> int:
    """Clear all entries in the disk cache. Returns number of removed files."""
    count = 0
    for f in os.listdir(CACHE_DIR):
        if f.endswith(".json") or f.endswith(".tmp"):
            try:
                os.remove(os.path.join(CACHE_DIR, f))
                count += 1
            except OSError:
                pass
    _CACHE_STATS["hits"] = 0
    _CACHE_STATS["misses"] = 0
    return count
