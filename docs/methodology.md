# FogSentinel Methodology Specification

## 1. N-BaIoT Dataset Ingestion & Validation

### 1.1 Source & Background
- **Source:** UCI Machine Learning Repository (DOI: `10.24432/C5RC8J`).
- **Research Authors:** Yair Meidan et al. (Ben-Gurion University & Singapore University of Technology and Design).
- **Scope:** Real traffic collected from commercial IoT devices authentically infected with Mirai and BASHLITE (gafgyt).
- **Target Device Evaluated:** Danmini Doorbell (1,018,298 total instances across 11 classes).

### 1.2 Structure of a Traffic Record
A single record is **NOT** a raw network packet or a device log. It represents a 115-dimensional vector of extracted statistical packet-stream metrics computed across decaying sliding windows (decay factors $\lambda = 5, 3, 1, 0.1, 0.01$):
- **Stream Aggregation Scopes:**
  - `H`: Host IP stats
  - `MI`: Source MAC-IP stats
  - `HH`: Host-to-Host (channel) stats
  - `HH_jit`: Channel jitter stats
  - `HpHp`: Host+Port to Host+Port (socket) stats
- **Statistical Features:** Weight (packet count), Mean packet size, Variance, Standard deviation, Radius, Magnitude, Covariance, and Pearson Correlation Coefficient (PCC).

---

## 2. Preprocessing & Leakage Prevention

1. **Schema Enforcement:** Input features are validated against `artifacts/feature_schema.json` containing the canonical 115 column names.
2. **Missing & Infinite Value Handling:** Any infinities or missing values are cleansed and imputed using clean column distributions.
3. **Leakage-Free Standard Scaling:**
   - The `StandardScaler` is fitted **strictly on the Training set**.
   - The saved scaler is then applied to validation, test, and live demonstration records.
4. **Data Partitioning:**
   - **Interactive Demo Set:** 55 records (5 benign + 5 per each of the 10 attack classes = 50 malicious records) set aside before model training.
   - **Training Set (70%):** 30,800 records.
   - **Validation Set (15%):** 6,600 records.
   - **Held-Out Test Set (15%):** 6,600 records.

---

## 3. Machine Learning Tasks

### Task A — Binary Classification
- **Classes:** `benign` vs. `malicious`.
- **Primary Goal:** Raise low-latency intrusion alert and initiate immediate containment recommendation.
- **Decision Policy:**
  - $P(\text{benign}) \ge 0.50 \implies \text{ALLOW}$
  - $P(\text{malicious}) > 0.50 \implies \text{QUARANTINE\_RECOMMENDED}$

### Task B — Multi-Class Classification (11 Classes)
- **Classes:**
  1. `benign`
  2. `gafgyt.combo`
  3. `gafgyt.junk`
  4. `gafgyt.scan`
  5. `gafgyt.tcp`
  6. `gafgyt.udp`
  7. `mirai.ack`
  8. `mirai.scan`
  9. `mirai.syn`
  10. `mirai.udp`
  11. `mirai.udpplain`

---

## 4. iFogSim2 Simulation Methodology

### 4.1 Parameter Sweep Design
- **Device Counts ($N_D$):** 10, 50, 100, 200 (4 levels)
- **Traffic Rates ($R_T$):** 1.0, 5.0 records/sec/device (2 levels)
- **One-Way WAN Latencies ($L_W$):** 25.0 ms, 100.0 ms, 200.0 ms (3 levels)
- **Placements ($P$):** Fog vs. Cloud (2 levels)
- **Total Configurations:** $4 \times 2 \times 3 \times 2 = 48$ scenarios.

### 4.2 Metrics Formulations
- **Mean Response Time:**
  $$\bar{T} = \frac{1}{N_{\text{completed}}} \sum_{i=1}^{N_{\text{completed}}} (T_{\text{actuator\_received}, i} - T_{\text{sensor\_emitted}, i})$$
- **WAN Bandwidth:**
  - $\text{WAN}_{\text{Fog}} = 0\text{ bytes}$
  - $\text{WAN}_{\text{Cloud}} = N_{\text{gen}} \times (920 + 40) + N_{\text{comp}} \times (128 + 40)\text{ bytes}$

