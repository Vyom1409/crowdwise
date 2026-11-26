import sys
import os
import asyncio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import plan_journey, match_stop

# Test stop matching
print('=== Stop Matching Tests ===')
for q in ['Badarpur', 'Kapashera', 'AIIMS', 'Kashmere Gate', 'Nehru Place', 'Anand Vihar', 'Dhaula Kuan', 'Red Fort']:
    matches = match_stop(q, limit=3)
    print(f'  {q:20s} -> {matches}')

# Test journey planning
print('\n=== Journey Plans ===')
test_cases = [
    ('Badarpur Border', 'Khanpur Extension / Devli Xing', 9, False),
    ('Badarpur', 'Kapashera', 8, False),
    ('AIIMS', 'Nehru Place', 9, False),
    ('Kashmere Gate', 'Badarpur', 18, False),
    ('Anand Vihar', 'Dhaula Kuan', 9, True),
]

async def run_tests():
    for orig, dest, hour, wknd in test_cases:
        result = await plan_journey(orig, dest, hour, wknd)
        day_type = "Weekend" if wknd else "Weekday"
        n = result.get("result_count", 0)
        print(f'\n  {orig} -> {dest} @ {hour:02d}:00 ({day_type}): {n} routes')
        for opt in result.get('options', [])[:3]:
            rid = opt["route_id"]
            tm = opt["est_time_mins"]
            dk = opt["distance_km"]
            cp = opt["crowdedness_pct"]
            ct = opt["comfort_text"]
            bc = opt["badge_color"]
            geom_pts = len(opt.get("road_geometry", []))
            is_app = opt.get("is_approximate", False)
            cached = opt.get("served_from_cache", False)
            print(f'    Bus {rid:10s} | {tm:3d}min | {dk:5.1f}km | {geom_pts} road pts | Approx:{is_app} Cached:{cached} | Crowd: {cp:5.1f}% ({ct})')

asyncio.run(run_tests())
