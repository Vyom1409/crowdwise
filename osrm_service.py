"""
OSRM Road Routing Service with Atomic Disk Cache, Waypoint Chunking & Resilience.
Provides road-snapped geometries, actual driving distances, and durations.
"""

import os
import json
import hashlib
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "backend", "osrm_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"
MAX_WAYPOINTS_PER_CHUNK = 18  # Safe under URL length & demo server waypoint limits
DEFAULT_TIMEOUT_SEC = 4.0
MAX_RETRIES = 2
BACKOFF_BASE_SEC = 0.4
USER_AGENT = "CrowdWise-Delhi/2.0 (hackathon-transit-routing)"


def _coords_to_cache_key(coords: List[List[float]], profile: str = "driving") -> str:
    """Generate deterministic SHA-256 cache key from exact coordinates, order, and profile."""
    repr_str = f"{profile}:" + ";".join(f"{float(c[0]):.5f},{float(c[1]):.5f}" for c in coords if len(c) >= 2)
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
            # Verify data integrity
            if data and isinstance(data, dict) and data.get("code") == "Ok" and "routes" in data:
                return data
    except Exception:
        pass
    return None


def _write_to_cache_atomic(cache_key: str, data: Dict[str, Any]) -> None:
    """Write valid response atomically to disk cache (temp file -> atomic rename)."""
    if not data or data.get("code") != "Ok" or not data.get("routes"):
        return  # Never cache failed, partial, or empty responses

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
        i += (max_chunk - 1)  # 1 overlapping point at boundary
    return chunks


async def _fetch_osrm_chunk_async(client: httpx.AsyncClient, chunk: List[List[float]]) -> Optional[Dict[str, Any]]:
    """Fetch road route for a single chunk with retry & backoff."""
    cache_key = _coords_to_cache_key(chunk)
    cached = _read_from_cache(cache_key)
    if cached:
        cached["_from_cache"] = True
        return cached

    # OSRM expects: {lng},{lat};{lng},{lat}...
    coord_param = ";".join(f"{c[1]:.5f},{c[0]:.5f}" for c in chunk)
    url = f"{OSRM_BASE_URL}/{coord_param}?overview=full&geometries=geojson"
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT_SEC)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    _write_to_cache_atomic(cache_key, data)
                    data["_from_cache"] = False
                    return data
            elif resp.status_code == 429:
                await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))
            else:
                break
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt < MAX_RETRIES:
                await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))

    return None


def _fetch_osrm_chunk_sync(chunk: List[List[float]]) -> Optional[Dict[str, Any]]:
    """Synchronous fetch for offline scripts or background tools."""
    cache_key = _coords_to_cache_key(chunk)
    cached = _read_from_cache(cache_key)
    if cached:
        cached["_from_cache"] = True
        return cached

    coord_param = ";".join(f"{c[1]:.5f},{c[0]:.5f}" for c in chunk)
    url = f"{OSRM_BASE_URL}/{coord_param}?overview=full&geometries=geojson"
    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(timeout=DEFAULT_TIMEOUT_SEC) as client:
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        _write_to_cache_atomic(cache_key, data)
                        data["_from_cache"] = False
                        return data
                elif resp.status_code == 429:
                    time.sleep(BACKOFF_BASE_SEC * (2 ** attempt))
                else:
                    break
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_BASE_SEC * (2 ** attempt))

    return None


async def get_road_route_async(coords: List[List[float]], fallback_dist_km: float = 0.0, fallback_mins: int = 0) -> Dict[str, Any]:
    """
    Given an ordered list of [lat, lon] coordinates, returns road-following geometry,
    accurate distance (km), duration (mins), and approximate fallback flags.
    Coordinates in road_geometry are returned in [lat, lon] order ready for Leaflet.
    """
    valid_coords = [c for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2 and c[0] is not None and c[1] is not None]
    if len(valid_coords) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": fallback_dist_km,
            "duration_mins": fallback_mins,
            "is_approximate": True,
            "fallback_reason": "Insufficient coordinates for routing (<2 stops)",
            "served_from_cache": False,
        }

    chunks = _chunk_coords(valid_coords)
    merged_geometry: List[List[float]] = []
    total_dist_meters = 0.0
    total_duration_sec = 0.0
    all_from_cache = True
    any_chunk_failed = False

    async with httpx.AsyncClient() as client:
        for idx, chunk in enumerate(chunks):
            result = await _fetch_osrm_chunk_async(client, chunk)
            if not result or result.get("code") != "Ok" or not result.get("routes"):
                any_chunk_failed = True
                break

            if not result.get("_from_cache", False):
                all_from_cache = False

            route_info = result["routes"][0]
            total_dist_meters += route_info.get("distance", 0.0)
            total_duration_sec += route_info.get("duration", 0.0)

            # OSRM coordinates are [lng, lat]. Invert to [lat, lng] for Leaflet!
            chunk_coords_leaflet = [[c[1], c[0]] for c in route_info["geometry"]["coordinates"]]

            if idx == 0:
                merged_geometry.extend(chunk_coords_leaflet)
            else:
                # Skip the first point of subsequent chunks to prevent duplicate junction vertices
                merged_geometry.extend(chunk_coords_leaflet[1:])

    if any_chunk_failed or len(merged_geometry) < 2:
        # Graceful fallback to straight-line stop connections with explicit warning flag
        return {
            "road_geometry": valid_coords,
            "distance_km": fallback_dist_km,
            "duration_mins": fallback_mins,
            "is_approximate": True,
            "fallback_reason": "Road routing engine unavailable (temporary network issue)",
            "served_from_cache": False,
        }

    road_dist_km = round(total_dist_meters / 1000.0, 1)
    road_duration_mins = max(1, int(round(total_duration_sec / 60.0)))

    return {
        "road_geometry": merged_geometry,
        "distance_km": road_dist_km,
        "duration_mins": road_duration_mins,
        "is_approximate": False,
        "fallback_reason": None,
        "served_from_cache": all_from_cache,
    }


def get_road_route_sync(coords: List[List[float]], fallback_dist_km: float = 0.0, fallback_mins: int = 0) -> Dict[str, Any]:
    """Synchronous version for offline cache generation / warmup scripts."""
    valid_coords = [c for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2 and c[0] is not None and c[1] is not None]
    if len(valid_coords) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": fallback_dist_km,
            "duration_mins": fallback_mins,
            "is_approximate": True,
            "fallback_reason": "Insufficient coordinates",
            "served_from_cache": False,
        }

    chunks = _chunk_coords(valid_coords)
    merged_geometry: List[List[float]] = []
    total_dist_meters = 0.0
    total_duration_sec = 0.0
    all_from_cache = True
    any_chunk_failed = False

    for idx, chunk in enumerate(chunks):
        result = _fetch_osrm_chunk_sync(chunk)
        if not result or result.get("code") != "Ok" or not result.get("routes"):
            any_chunk_failed = True
            break

        if not result.get("_from_cache", False):
            all_from_cache = False

        route_info = result["routes"][0]
        total_dist_meters += route_info.get("distance", 0.0)
        total_duration_sec += route_info.get("duration", 0.0)

        chunk_coords_leaflet = [[c[1], c[0]] for c in route_info["geometry"]["coordinates"]]

        if idx == 0:
            merged_geometry.extend(chunk_coords_leaflet)
        else:
            merged_geometry.extend(chunk_coords_leaflet[1:])

    if any_chunk_failed or len(merged_geometry) < 2:
        return {
            "road_geometry": valid_coords,
            "distance_km": fallback_dist_km,
            "duration_mins": fallback_mins,
            "is_approximate": True,
            "fallback_reason": "Road routing engine unavailable",
            "served_from_cache": False,
        }

    return {
        "road_geometry": merged_geometry,
        "distance_km": round(total_dist_meters / 1000.0, 1),
        "duration_mins": max(1, int(round(total_duration_sec / 60.0))),
        "is_approximate": False,
        "fallback_reason": None,
        "served_from_cache": all_from_cache,
    }


def clear_cache(older_than_seconds: Optional[int] = None) -> int:
    """Clear bad or stale cache entries; returns count of deleted files."""
    if not os.path.exists(CACHE_DIR):
        return 0
    now = time.time()
    deleted = 0
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".json") or fname.endswith(".tmp"):
            fpath = os.path.join(CACHE_DIR, fname)
            try:
                if older_than_seconds is None or (now - os.path.getmtime(fpath)) > older_than_seconds:
                    os.remove(fpath)
                    deleted += 1
            except OSError:
                pass
    return deleted
