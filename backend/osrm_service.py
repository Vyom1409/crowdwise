"""
OSRM Road Routing Service - Backward-compatible wrapper delegating to backend.routing.osrm_client.
"""

from backend.routing.osrm_client import (
    get_road_route_async,
    get_road_route_sync,
    get_table_async,
    get_cache_stats,
    clear_cache,
    CACHE_DIR,
    OSRM_BASE_URL,
)

__all__ = [
    "get_road_route_async",
    "get_road_route_sync",
    "get_table_async",
    "get_cache_stats",
    "clear_cache",
    "CACHE_DIR",
    "OSRM_BASE_URL",
]
