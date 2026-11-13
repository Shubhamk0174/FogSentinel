# FogSentinel Architecture Specification

## 1. System Topology

FogSentinel implements a three-tier hierarchical computing architecture:

```text
                           +-------------------------------------+
                           |            Cloud Server             |
                           |   (44,800 MIPS, 40 GB RAM)         |
                           +-------------------------------------+
                                              ^
                                              | WAN Link (25 / 100 / 200 ms latency)
                                              v
                           +-------------------------------------+
                           |          Fog Gateway                |
                           |   (4,000 MIPS, 8 GB RAM)            |
                           +-------------------------------------+
                                     /        |        \
                                    /         |         \  LAN Link (2 ms latency)
                                   v          v          v
                           +---------+   +---------+   +---------+
                           |  IoT-1  |   |  IoT-2  |   |  IoT-N  |
                           | (500 M) |   | (500 M) |   | (500 M) |
                           +---------+   +---------+   +---------+
                              |   ^         |   ^         |   ^
                              v   |         v   |         v   |  Device Bus (1 ms)
                           [Sensor][Actuator]...
```

### 1.1 Physical Entities
- **Cloud Server:** High-capacity compute center (44,800 MIPS, 40 GB RAM) with 100 Mbps uplink and 10 Gbps downlink bandwidth. Host power: 16 × 103 W (busy), 16 × 83.25 W (idle).
- **Fog Gateway:** Intermediate local server (4,000 MIPS, 8 GB RAM) located on the edge network. Host power: 107.339 W (busy), 83.4333 W (idle).
- **IoT Endpoints:** Low-power embedded endpoints (500 MIPS, 1 GB RAM, e.g., smart cameras, doorbells, thermostats). Host power: 87.53 W (busy), 82.44 W (idle).

### 1.2 Communication Links
- **IoT-to-Gateway Link:** Local Ethernet/Wi-Fi LAN link with **2.0 ms one-way latency** and 10 Gbps bandwidth.
- **Gateway-to-Cloud Link:** Long-haul Internet WAN link with variable one-way latency (**25.0 ms, 100.0 ms, 200.0 ms**) and 100 Mbps bandwidth.
- **Device Internal Bus:** Sensor/actuator device bus with **1.0 ms latency**.

---

## 2. Distributed Data Flow (DDF) Application Model

The application graph consists of:
- **Module:** `classifier_service` (20 MB RAM requirement, 1,000 MIPS computational workload).
- **Sensor Edge:** `IOT_TRAFFIC` (Direction: `Tuple.UP`, Payload: 920 bytes for 115 float64 features, Workload: 1,000 MIPS).
- **Actuator Edge:** `SECURITY_ALERT` (Direction: `Tuple.DOWN`, Payload: 128 bytes alert message, Workload: 50 MIPS).
- **Selectivity:** 1.0 (1 incoming `IOT_TRAFFIC` tuple emits 1 outgoing `SECURITY_ALERT` tuple).
- **Application Loop:** `[IOT_TRAFFIC -> classifier_service -> SECURITY_ALERT]` continuously monitored by `TimeKeeper`.

---

## 3. Placement Configurations

| Parameter | Fog-Side Placement | Cloud-Side Placement |
| :--- | :--- | :--- |
| **Module Location** | `fog-gateway` | `cloud` |
| **Inspection Path** | IoT -> Fog Gateway -> IoT Actuator | IoT -> Fog Gateway -> Cloud -> Fog Gateway -> IoT Actuator |
| **One-Way Network Hops** | 2 ms LAN | 2 ms LAN + 100 ms WAN |
| **Round-Trip Delay** | ~4-10 ms | ~204-212 ms |
| **WAN Bandwidth Used** | **0 KB** (strictly local) | **960 bytes uplink + 168 bytes downlink per record** |

---

## 4. Integration Bridge Between Python ML & iFogSim2

1. **Python ML Pipeline:**
   - Preprocesses raw N-BaIoT 115-feature vectors.
   - Evaluates records using trained neural network / ensemble classifiers.
   - Emits predictions to `outputs/demo/demo_predictions.csv` and manifest to `outputs/demo/workload_manifest.csv`.
2. **Bridge Interface:**
   - Manifest supplies record ID, detection action (`ALLOW` vs `QUARANTINE_RECOMMENDED`), instruction length (1,000 MIPS), and payload sizes.
3. **Java Simulator:**
   - Reads workload specifications and simulates execution timing, queueing delays, network traversal, and power consumption under both Fog and Cloud topologies.

