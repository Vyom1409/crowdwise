"""
Unit tests for RAPTOR transit routing algorithm and crowd-aware trade-offs.
Tests on a controlled toy transit network.
"""

import unittest
from backend.routing.raptor import TransitNetwork, RaptorRouter


class TestRaptorToyNetwork(unittest.TestCase):
    def setUp(self):
        """Construct a hand-crafted toy transit network."""
        self.network = TransitNetwork()

        # 6 Stops
        self.network.stops = {
            "Stop_A": {"stop_name": "Stop_A", "lat": 28.500, "lon": 77.200, "total_activity": 100},
            "Stop_B": {"stop_name": "Stop_B", "lat": 28.510, "lon": 77.200, "total_activity": 80},
            "Stop_C": {"stop_name": "Stop_C", "lat": 28.520, "lon": 77.200, "total_activity": 90},
            "Stop_D": {"stop_name": "Stop_D", "lat": 28.530, "lon": 77.200, "total_activity": 110},
            "Stop_E": {"stop_name": "Stop_E", "lat": 28.515, "lon": 77.250, "total_activity": 50},
            "Stop_F": {"stop_name": "Stop_F", "lat": 28.511, "lon": 77.201, "total_activity": 60},  # ~120m from B
        }

        for s in self.network.stops:
            self.network.normalized_stop_index[s.lower()] = s

        # Footpath between Stop_B and Stop_F (~2 mins walk)
        self.network.footpaths["Stop_B"].append(("Stop_F", 2, 120.0))
        self.network.footpaths["Stop_F"].append(("Stop_B", 2, 120.0))

        # Route Fast_1: Stop_A -> Stop_B -> Stop_C
        # Crowdedness: 80% (packed, high speed)
        self.network.routes["Route_Fast_1"] = {
            "route_id": "Route_Fast_1",
            "route_name": "Fast Line 1",
            "direction": "Northbound",
            "stops": ["Stop_A", "Stop_B", "Stop_C"],
            "stop_indices": {"Stop_A": 0, "Stop_B": 1, "Stop_C": 2},
            "offsets": [0, 8, 16],  # 8 min per stop
            "departures": [540, 555, 570],  # 09:00, 09:15, 09:30
            "hourly_crowdedness_weekday": [80.0] * 24,
            "hourly_crowdedness_weekend": [80.0] * 24,
            "segment_load_factors": [1.0, 1.0, 1.0],
            "is_ac": True,
            "fare": 15.0,
        }

        # Route Fast_2: Stop_C -> Stop_D
        # Connects with Route_Fast_1 at Stop_C
        self.network.routes["Route_Fast_2"] = {
            "route_id": "Route_Fast_2",
            "route_name": "Fast Line 2",
            "direction": "Northbound",
            "stops": ["Stop_C", "Stop_D"],
            "stop_indices": {"Stop_C": 0, "Stop_D": 1},
            "offsets": [0, 8],  # 8 min
            "departures": [558, 573, 588],  # 09:18 connects smoothly after arrival at 09:16
            "hourly_crowdedness_weekday": [80.0] * 24,
            "hourly_crowdedness_weekend": [80.0] * 24,
            "segment_load_factors": [1.0, 1.0],
            "is_ac": True,
            "fare": 15.0,
        }

        # Route Slow_Comfortable: Stop_A -> Stop_E -> Stop_D (Direct, uncrowded, but slower)
        # Crowdedness: 18% (seats available, calm journey, 32 min total travel)
        self.network.routes["Route_Slow_Comfortable"] = {
            "route_id": "Route_Slow_Comfortable",
            "route_name": "Scenic Slow Line",
            "direction": "Northbound",
            "stops": ["Stop_A", "Stop_E", "Stop_D"],
            "stop_indices": {"Stop_A": 0, "Stop_E": 1, "Stop_D": 2},
            "offsets": [0, 16, 34],  # 34 mins total
            "departures": [540, 560, 580],  # 09:00 departure
            "hourly_crowdedness_weekday": [18.0] * 24,
            "hourly_crowdedness_weekend": [18.0] * 24,
            "segment_load_factors": [1.0, 1.0, 1.0],
            "is_ac": False,
            "fare": 10.0,
        }

        # Inverted index
        for r_id, r in self.network.routes.items():
            for s in r["stops"]:
                self.network.stop_to_routes[s].append(r_id)

        self.network.is_built = True
        self.router = RaptorRouter(self.network)

    def test_direct_route_found(self):
        """Test finding a direct route without transfers."""
        res = self.router.query("Stop_A", "Stop_C", dep_time_mins=540, max_transfers=0)
        self.assertGreater(len(res["journeys"]), 0)
        j = res["journeys"][0]
        self.assertEqual(j["transfers"], 0)
        self.assertEqual(j["legs"][0]["route_id"], "Route_Fast_1")
        self.assertEqual(j["arrival_time"], "09:16")

    def test_one_transfer_route(self):
        """Test finding a route requiring exactly 1 transfer (Stop_A -> Stop_D via Stop_C)."""
        res = self.router.query("Stop_A", "Stop_D", dep_time_mins=540, max_transfers=1, mode="fastest")
        self.assertGreater(len(res["journeys"]), 0)
        fast_journey = res["journeys"][0]
        # Fast transfer route: arrives at 09:26 (26 mins total)
        self.assertEqual(fast_journey["arrival_time"], "09:26")
        self.assertEqual(fast_journey["transfers"], 1)
        self.assertEqual(len([l for l in fast_journey["legs"] if l["type"] == "bus"]), 2)

    def test_crowd_aware_preference_tradeoff(self):
        """
        Test that when mode='fastest', the faster crowded route is chosen first,
        and when mode='least_crowded', the slower uncrowded direct route is chosen first.
        """
        # Under 'fastest':
        res_fast = self.router.query("Stop_A", "Stop_D", dep_time_mins=540, max_transfers=1, mode="fastest")
        top_fast = res_fast["journeys"][0]
        self.assertEqual(top_fast["total_duration_mins"], 26)  # Fast 26 min option wins
        self.assertEqual(top_fast["avg_crowdedness_pct"], 80.0)

        # Under 'least_crowded':
        res_comfort = self.router.query("Stop_A", "Stop_D", dep_time_mins=540, max_transfers=1, mode="least_crowded")
        top_comfort = res_comfort["journeys"][0]
        self.assertEqual(top_comfort["avg_crowdedness_pct"], 18.0)  # Calm 18% option wins
        self.assertEqual(top_comfort["total_duration_mins"], 34)  # Slower (34 min) but selected for comfort!

    def test_footpath_transfer(self):
        """Test that transfer footpaths between nearby stops are relaxed."""
        self.assertIn("Stop_F", [n[0] for n in self.network.footpaths["Stop_B"]])


if __name__ == "__main__":
    unittest.main()
