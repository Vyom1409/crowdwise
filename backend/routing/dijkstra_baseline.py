"""
Dijkstra Transit Routing Baseline
Provides a standard time-dependent shortest-path baseline algorithm for benchmarking against RAPTOR.
"""

import heapq
import time
import bisect
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from backend.routing.raptor import TransitNetwork


class DijkstraRouter:
    """
    Standard earliest-arrival Dijkstra baseline router on transit network.
    Used for algorithmic benchmark comparisons against RAPTOR.
    """

    def __init__(self, network: TransitNetwork):
        self.network = network

    def query(self, origin_stop: str, dest_stop: str, dep_time_mins: int = 540) -> Dict[str, Any]:
        """
        Executes standard Dijkstra search to find the earliest arrival time at dest_stop.
        Returns execution metrics including query time, nodes settled, and edges relaxed.
        """
        t0 = time.perf_counter()

        if origin_stop not in self.network.stops or dest_stop not in self.network.stops:
            return {"error": "Stop not found", "query_time_ms": 0.0, "nodes_settled": 0}

        # Min-heap queue of (arrival_time, current_stop)
        queue: List[Tuple[int, str]] = [(dep_time_mins, origin_stop)]
        visited: Dict[str, int] = {origin_stop: dep_time_mins}
        nodes_settled = 0
        edges_relaxed = 0

        while queue:
            curr_time, curr_stop = heapq.heappop(queue)
            nodes_settled += 1

            if curr_stop == dest_stop:
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
                return {
                    "algorithm": "Dijkstra (Time-Expanded Baseline)",
                    "origin": origin_stop,
                    "destination": dest_stop,
                    "departure_time_mins": dep_time_mins,
                    "arrival_time_mins": curr_time,
                    "total_duration_mins": curr_time - dep_time_mins,
                    "nodes_settled": nodes_settled,
                    "edges_relaxed": edges_relaxed,
                    "query_time_ms": elapsed_ms,
                    "found": True,
                }

            if curr_time > visited.get(curr_stop, float("inf")):
                continue

            # 1. Relax transit edges (routes passing through curr_stop)
            for r_id in self.network.stop_to_routes.get(curr_stop, []):
                r_info = self.network.routes[r_id]
                stops = r_info["stops"]
                offsets = r_info["offsets"]
                departures = r_info["departures"]
                curr_idx = r_info["stop_indices"][curr_stop]
                curr_offset = offsets[curr_idx]

                # Find next earliest trip on this route departing >= curr_time
                needed_dep = curr_time - curr_offset
                dep_idx = bisect.bisect_left(departures, needed_dep)
                if dep_idx >= len(departures):
                    continue

                trip_dep = departures[dep_idx]

                # Traverse subsequent stops along this route
                for nxt_idx in range(curr_idx + 1, len(stops)):
                    nxt_stop = stops[nxt_idx]
                    nxt_arr = trip_dep + offsets[nxt_idx]
                    edges_relaxed += 1

                    if nxt_arr < visited.get(nxt_stop, float("inf")):
                        visited[nxt_stop] = nxt_arr
                        heapq.heappush(queue, (nxt_arr, nxt_stop))

            # 2. Relax walking transfer footpaths
            for neighbor, walk_m, _ in self.network.footpaths.get(curr_stop, []):
                nxt_arr = curr_time + walk_m
                edges_relaxed += 1
                if nxt_arr < visited.get(neighbor, float("inf")):
                    visited[neighbor] = nxt_arr
                    heapq.heappush(queue, (nxt_arr, neighbor))

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "algorithm": "Dijkstra (Time-Expanded Baseline)",
            "origin": origin_stop,
            "destination": dest_stop,
            "departure_time_mins": dep_time_mins,
            "arrival_time_mins": visited.get(dest_stop, -1),
            "total_duration_mins": -1,
            "nodes_settled": nodes_settled,
            "edges_relaxed": edges_relaxed,
            "query_time_ms": elapsed_ms,
            "found": dest_stop in visited,
        }
