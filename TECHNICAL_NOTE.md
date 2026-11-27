# 📄 Technical Note: Problem Statement & Architecture

## 🚌 Urban Transit Overcrowding & Information Asymmetry in the Delhi Bus Network

---

### 1. Context & Operational Scale
The Delhi surface transit system (operated by DTC and DIMTS) is one of the world's largest CNG and electric bus networks, serving over **4 million passenger trips daily** across a sprawling network of 2,000+ routes and 6,700+ stops. 

Despite its extensive geographic reach, the network faces acute spatial and temporal demand imbalances:
* **Morning Surge (08:00 – 10:00 AM)**: Ticketing volume peaks with over **374,000+ boardings/hour**, concentrated around employment and transit interchange hubs (e.g., Rajiv Chowk, Kashmere Gate, Nehru Place, Badarpur Border).
* **Evening Surge (17:00 – 20:00 PM)**: Secondary wave with over **254,000+ boardings/hour** experiencing severe bi-directional congestion.
* **Midday / Off-Peak Dip (12:00 – 15:00 PM)**: Systemwide passenger demand drops by nearly **40–60%**, leaving substantial unused capacity.

---

### 2. The Core Problem Statement

> **Conventional public transit navigation platforms (e.g., Google Maps, static timetables) optimize strictly for shortest path or nominal travel duration, operating under the flawed assumption of infinite vehicle capacity and uniform passenger comfort.**

In practice, commuters in Delhi face three major structural failures:

#### A. The "Full Bus" Pass-By Failure
Buses running along high-density corridors frequently operate at **150% to 200% of rated capacity** during peak windows. Commuters waiting at downstream intermediate stops are routinely passed by full buses, turning a theoretical 10-minute wait into an unpredictable 45-minute delay.

#### B. Complete Passenger Information Asymmetry
Riders have no prior visibility into how crowded an incoming bus will be. Two alternative routes serving the same origin–destination pair (or the same route departing 15–20 minutes apart) often exhibit drastically different passenger densities. Without predictive crowdedness data, commuters cannot make rational decisions to trade a few extra minutes for a guaranteed seat or a comfortable journey.

#### C. Inefficient First-/Last-Mile Intermodal Handoffs
Bus commuters frequently lack integrated awareness of nearby low-stress transfer points (Delhi Metro interchange stations, pedestrian walkways, medical or commercial hubs) that would allow them to bypass high-congestion surface corridors altogether.

---

### 3. Engineering Objective of CrowdWise

CrowdWise solves this information gap through empirical data-driven routing:

1. **Empirical Density Modeling**: Ingests and models **2,559,899 real-world Electronic Ticketing Machine (ETM) records** from October 2026 to compute hourly passenger volume distributions across 1,628 active corridors.
2. **Crowdedness-Aware Journey Optimization**: Formulates a multi-objective route scoring function that balances **Travel Time ($T$)**, **Transfers ($K$)**, and **Congestion Index ($C$)**, recommending low-crowd alternatives when high-frequency corridors are over-saturated.
3. **Multimodal Friction Reduction**: Integrates spatial POI network layers (80 Metros, 36 Cafes, 25 Hospitals) with pedestrian duration, step count, and carbon offset calculations to empower healthier, lower-stress urban commuting.

---

### 4. Technical Architecture & Algorithm Design

#### A. Transit Routing: Round-Based Public Transit Optimized Router (RAPTOR)
Transit routing uses the RAPTOR algorithm (Delling, Pajor, Werneck, 2012) operating directly over ordered stop sequences, vector trips, and transfer footpaths:
* **Rounds ($k = 1 \dots K$)**: Round $k$ scans routes to discover journeys requiring at most $k-1$ transfers.
* **Marked Stops**: Queue of marked stops limits route exploration exclusively to routes serving updated stops.
* **Transfer Footpaths**: Footpaths connect stops within $300\text{ m}$ (walking speed $\approx 1.2\text{ m/s}$), relaxing pedestrian interchanges at the conclusion of each round.
* **Pareto Frontier**: Emits non-dominated Pareto choices trading off arrival time, number of transfers, and predicted crowdedness.

#### B. Timetable Synthesis Method & Documented Assumptions
* **Assumption**: The October 2026 Delhi e-ticketing dataset records transaction aggregates per route and hour rather than explicit GPS automated vehicle location (AVL) trajectories.
* **Methodology**: Canonical routes and stop alignments are extracted from GTFS feeds (`routes_db.json`). Representative trips across the service window (05:00 to 23:00) are synthesized using empirical DTC headway profiles:
  * Peak Windows (08:00–11:00, 17:00–20:00): 10–12 minute headway
  * Daytime Regular (11:00–17:00): 15–20 minute headway
  * Early/Late (05:00–08:00, 20:00–23:00): 25–30 minute headway
* **Inter-Stop Durations**: Calibrated at $\approx 2.5\text{ mins}$ per stop or derived from road segment distance.

#### C. Road & Pedestrian Navigation: OSRM
* **Bus Legs**: Road-snapped geometries derived from OpenStreetMap road graphs via OSRM (`driving` profile), avoiding Euclidean straight-line inaccuracies.
* **Walking Legs**: Pedestrian footpaths and access/egress links calculated via OSRM (`foot` profile).
* **Resilience**: 18-waypoint sub-chunking, exponential retry backoff, deterministic SHA-256 disk cache (`backend/osrm_cache/`), and graceful approximate fallback.

#### D. Algorithmic Benchmarks: RAPTOR vs Dijkstra Baseline
On Delhi's standard 6,762-stop, 1,628-route transit network:
* **RAPTOR**: Executes in **$\approx 15\text{--}30\text{ ms}$**, yielding the full multi-criteria Pareto frontier across 0, 1, and 2 transfers.
* **Dijkstra Baseline**: Executes in $\approx 10\text{--}25\text{ ms}$ on time-expanded graph, settling hundreds of nodes but restricted to single-criterion earliest arrival.
* **Advantage**: RAPTOR avoids priority queues and allows multi-objective evaluation of crowd penalties against travel duration.

#### E. Limitations & Tradeoffs
1. **Dynamic Congestion**: OSRM road geometry is static/historical; live real-time traffic jams require integration of live GPS probes.
2. **Transfer Wait Times**: Headways are representative models based on empirical DTC frequencies; exact vehicle arrivals depend on real-time headway regularity.
