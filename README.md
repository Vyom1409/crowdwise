# 🚌 CrowdWise — Crowdedness-Aware Delhi Bus Journey Planner

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**CrowdWise** is an intelligent, crowdedness-aware urban transit journey planner designed specifically for the Delhi Bus Transit Network. Built on analysis of **2,559,899 ticketing records** from the Delhi Open Transit Dataset (October 2026), CrowdWise models passenger density across **1,628 routes** and **6,762 stops**, powered by the **RAPTOR** algorithm and **OSRM** road routing to deliver multi-objective, low-stress transit itineraries.

---

## 🎯 Problem Statement & Proposal

> 📑 **Read the complete docs**: [Full Project Proposal (PROPOSAL.md)](PROPOSAL.md) • [Technical Note (TECHNICAL_NOTE.md)](TECHNICAL_NOTE.md)

### 1. Problem We Chose
Conventional public transit journey planners (e.g., Google Maps) optimize strictly for **shortest path or theoretical duration**, implicitly assuming infinite vehicle capacity and uniform passenger comfort.

In Delhi (DTC/DIMTS), where over **4 million passenger trips occur daily**, this causes severe real-world failures:
* **The "Full Bus" Pass-By**: Buses reach $150\%\text{--}200\%$ capacity during morning ($08:00\text{--}10:00$) and evening ($17:00\text{--}20:00$) surges, skipping intermediate stops and stranding commuters.
* **Information Asymmetry**: Commuters cannot see whether an approaching bus is crush-loaded, missing calmer alternative buses departing just 10–15 minutes apart.
* **Network-Wide Overload**: Passenger demand concentrates on a few popular corridors while parallel routes run under-capacity.

### 2. Our Approach
* **RAPTOR Transit Routing**: Round-bAsed Public Transit Optimized Router calculates earliest arrival and transfer combinations across all 1,628 Delhi routes in $<30\text{ms}$.
* **OSRM Road & Walking Legs**: Replaces straight lines with real road curves and walking paths, displaying road distance and duration.
* **Multi-Criteria Optimization**: Recommends Pareto-optimal journeys with mode choices: **⚡ Fastest**, **⚖️ Balanced**, or **🪑 Least Crowded**.
* **Step-by-Step Itineraries**: Expandable timeline showing exact board/alight stops, walking segments, transfer junctions, and crowd badges.
* **Multimodal Integration**: Connects bus routes with 80 Delhi Metro stations, cafes, and hospitals, showing walking minutes, calorie burn, and carbon offset.

---

## ✨ Features

- 🧭 **RAPTOR Algorithm (`backend/routing/raptor.py`)**: Vector timetable scanning with transfer relaxation (footpaths $\le 300\text{m}$) and $K$-round Pareto frontier construction.
- 🛣️ **OSRM Road Navigation (`backend/routing/osrm_client.py`)**: Road-following geometries for bus legs (colored by crowdedness) and dashed lines for walking legs, backed by atomic SHA-256 disk caching in `backend/osrm_cache/`.
- 📊 **Empirical Crowdedness Models**: Grounded on 2.56M ETM tickets ($R^2 = 0.8981$, $\text{MAE} = 4.50$ passengers/hr, $+65.8\%$ accuracy gain vs static timetables).
- 🔬 **Algorithmic Benchmarks**: Live comparison of RAPTOR vs Time-Expanded Dijkstra baseline directly in the telemetry modal.
- 🐳 **Self-Hosted OSRM Support**: Includes `docker-compose.yml` for offline local routing with an India/Delhi OSM extract.
- ⚡ **One-Click Startup (`START.bat`)**: Fully automated Windows launcher that verifies Python, auto-installs dependencies, dynamically detects the port, and automatically opens the website in Google Chrome.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    Client["Frontend (index.html)<br>Leaflet.js + Chart.js"]
    API["FastAPI Backend (app.py)<br>POST /api/plan"]
    RAPTOR["RAPTOR Transit Router<br>(backend/routing/raptor.py)"]
    Dijkstra["Dijkstra Baseline<br>(backend/routing/dijkstra_baseline.py)"]
    OSRM["OSRM Client<br>(backend/routing/osrm_client.py)"]
    Cache[("Disk Cache<br>backend/osrm_cache/*.json")]
    Data[("Precomputed DBs<br>routes_db.json / stops_db.json")]

    Client -->|POST /api/plan| API
    API -->|Query Transit Timetable| RAPTOR
    RAPTOR -->|Stop Sequences & Trips| Data
    API -->|Enrich Road & Walking Geometry| OSRM
    OSRM -->|SHA-256 Check| Cache
    OSRM -->|Fetch Uncached| RemoteOSRM["OSRM Server (router.project-osrm.org or Docker)"]
    API -->|Algorithmic Benchmark| Dijkstra
    API -->|Pareto Journeys + Legs + Road Geometries| Client
```

---

## 🚀 Quickstart & Setup

> 🌐 **Direct Website Link (once the server is running):** <a href="http://127.0.0.1:8765" target="_blank" rel="noopener noreferrer">http://127.0.0.1:8765</a>

### Option 1: Automated Launcher (Windows)
Double-click **`START.bat`** in the repository root. It will:
1. Detect Python and install required packages from `requirements.txt`.
2. Launch the FastAPI server on <a href="http://127.0.0.1:8765" target="_blank" rel="noopener noreferrer">http://127.0.0.1:8765</a>.
3. Open Google Chrome automatically.

### Option 2: Manual Terminal Run
```bash
# Clone the repository
git clone https://github.com/Vyom1409/crowdwise.git
cd crowdwise

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```
Open <a href="http://127.0.0.1:8765" target="_blank" rel="noopener noreferrer"><strong>http://127.0.0.1:8765</strong></a> in your browser:

[![Open CrowdWise in Browser](https://img.shields.io/badge/Open_CrowdWise_Website-http%3A%2F%2F127.0.0.1%3A8765-3b82f6?style=for-the-badge&logo=googlechrome&logoColor=white)](http://127.0.0.1:8765)

---

## 🐳 Self-Hosting OSRM with Docker Compose

By default, CrowdWise connects to the public OSRM demo server (`http://router.project-osrm.org`) with local disk caching. To run completely offline or without public rate limits:

```bash
# 1. Create OSRM data directory
mkdir osrm_data

# 2. Download Delhi / Northern India extract from Geofabrik
curl -o osrm_data/delhi-latest.osm.pbf https://download.geofabrik.de/asia/india/northern-zone-latest.osm.pbf

# 3. Extract, partition, and customize the road network
docker run -t -v "${PWD}/osrm_data:/data" ghcr.io/project-osrm/osrm-backend osrm-extract -p /opt/car.lua /data/delhi-latest.osm.pbf
docker run -t -v "${PWD}/osrm_data:/data" ghcr.io/project-osrm/osrm-backend osrm-partition /data/delhi-latest.osrm
docker run -t -v "${PWD}/osrm_data:/data" ghcr.io/project-osrm/osrm-backend osrm-customize /data/delhi-latest.osrm

# 4. Start the local OSRM routing service
docker compose up -d

# 5. Point CrowdWise to the local OSRM service
export OSRM_BASE_URL=http://localhost:5000   # Linux/macOS
set OSRM_BASE_URL=http://localhost:5000      # Windows CMD
$env:OSRM_BASE_URL="http://localhost:5000"  # Windows PowerShell
python app.py
```

---

## 📡 API Reference

### Plan Journey (RAPTOR + OSRM + Crowd-Aware)
* **Endpoint**: `POST /api/plan` (also supports `GET /api/plan`)
* **Request Body**:
```json
{
  "origin": "Badarpur Border",
  "destination": "Khanpur Extension / Devli Xing",
  "depart_time": "09:00",
  "mode": "balanced",
  "max_transfers": 2,
  "weekend": false
}
```
* **Modes**:
  * `fastest`: Minimizes total travel duration.
  * `least_crowded`: Maximizes seat availability and passenger comfort.
  * `balanced`: Optimal multi-objective trade-off between time, transfers, and crowdedness.
* **Response**: Returns a Pareto set of journeys with step-by-step legs (`bus` with road geometry and crowdedness %, `walk` with distance and duration), total duration, transfers count, calorie burn, and nearest POIs.

### Benchmarks & Algorithmic Telemetry
* **Endpoint**: `GET /api/benchmark/metrics`
* **Response**: Returns live RAPTOR query time, rounds executed, Pareto frontier count, Dijkstra baseline comparison (query time, nodes settled, edges relaxed), OSRM cache hit rate %, and empirical model validation stats ($R^2$, MAE).

---

## 🧪 Testing

```bash
# Run RAPTOR toy network unit tests (transfer & crowd-aware trade-offs)
python test_raptor.py

# Run transit engine and stop matching integration tests
python test_engine.py

# Run planner sanity test
python test_planner.py
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
