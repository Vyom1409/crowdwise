"""
OSRM Road Routing Service - Root wrapper delegating to backend.routing.osrm_client.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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
