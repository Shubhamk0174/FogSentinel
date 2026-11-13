# FogSentinel — Faculty Viva Examination Guide & Model Answers

### Q1: What is the core objective of the FogSentinel project?
**Answer:** FogSentinel investigates two interconnected questions in IoT security:
1. **Detection:** Can a machine-learning model identify malicious IoT botnet traffic from high-dimensional statistical network features?
2. **Placement:** If a security alert/action must be generated, what are the empirical trade-offs in response latency, WAN bandwidth, and energy when placing the detection module locally on a Fog Gateway versus in a centralized Remote Cloud Data Centre?

---

### Q2: What dataset did you use, and what is its source?
**Answer:** We used the official **N-BaIoT (Network-Based Detection of IoT Botnet Attacks)** dataset from the UCI Machine Learning Repository (DOI: `10.24432/C5RC8J`), published by Yair Meidan et al. in 2018. It contains real network traffic from nine commercial IoT devices infected with Mirai and BASHLITE (gafgyt).

---

### Q3: What represents one record in the dataset? Is it a packet?
**Answer:** **No, a record is NOT a single packet.** A record is a 115-dimensional vector of derived statistical metrics (packet stream weights, mean sizes, variance, standard deviation, jitter, covariance, and radii) computed over sliding decaying time windows ($\lambda = 5, 3, 1, 0.1, 0.01$).

---

### Q4: Explain the input dimensions used in the demonstration.
**Answer:**
- **55 Records:** 55 selected demonstration rows (5 benign + 5 per each of the 10 attack classes = 50 attack rows).
- **115 Features:** Each record has 115 continuous numerical feature measurements.
- Therefore, the demo input feature matrix is **$55 \times 115$**, completely separate from labels.

---

### Q5: How did you prevent data leakage?
**Answer:**
1. The 55-record demonstration dataset was partitioned and saved **prior** to model training.
2. The remaining data was split into **Training (70%)**, **Validation (15%)**, and **Held-Out Testing (15%)**.
3. The `StandardScaler` was **fitted strictly on the Training set only**, then applied to validation, test, and demo records.

---

### Q6: What models did you evaluate, and which performed best?
**Answer:** We compared a linear baseline (Logistic Regression), a non-linear ensemble baseline (Random Forest), and a multi-layer feed-forward neural network (MLP: Dense(64) + ReLU + Dense(32) + ReLU). On our held-out test set (6,600 unseen records), the **Random Forest** achieved 99.98% binary accuracy and 99.98% multi-class accuracy, while the **MLP** achieved 99.97% binary accuracy and 90.71% multi-class accuracy.

---

### Q7: What is iFogSim2, and does it execute your Python code?
**Answer:** iFogSim2 is an open-source Java/CloudSim-based toolkit developed by Cloudslab (University of Melbourne) for modeling and simulating resource management in Edge and Fog environments. **iFogSim2 does NOT train or execute the Python neural network.** iFogSim2 simulates the physical topology, CPU MIPS execution, packet queueing, and network propagation delays. The Python pipeline and Java simulator are connected via an exported workload manifest bridge.

---

### Q8: Why does Fog placement achieve ~9.38 ms while Cloud takes ~206.98 ms?
**Answer:**
- In **Cloud placement**, network traffic must traverse the long-haul WAN link: 2 ms (LAN to gateway) + 100 ms (WAN uplink to Cloud) + Cloud processing delay + 100 ms (WAN downlink back to gateway) + 2 ms (LAN to IoT actuator) + 1 ms bus $\approx 206-212\text{ ms}$.
- In **Fog placement**, the classifier executes directly on the Fog Gateway: 2 ms (LAN to gateway) + Fog processing delay + 2 ms (LAN back to IoT actuator) + 1 ms bus $\approx 9.38\text{ ms}$.
- Fog placement saves **over 95% of response latency**.

---

### Q9: Does Fog computing always save energy?
**Answer:** **No.** As established in our empirical simulation results and noted in the project specification, energy savings depend heavily on the device idle power, active power model, and load distribution. A fog gateway remaining powered on continuously with small workloads can sometimes consume more aggregate power than high-density cloud data centers.

---

### Q10: Does FogSentinel actually isolate physical devices on your network?
**Answer:** **No.** FogSentinel is an academic prototype and simulation. The decision output is `QUARANTINE_RECOMMENDED` or simulated. Real-world physical isolation would require an SDN OpenFlow controller (e.g., Ryu, ONOS) sending packet-drop rules to physical network switches.

