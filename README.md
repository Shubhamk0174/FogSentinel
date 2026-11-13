# FogSentinel — IoT Network-Traffic Monitoring and Fog-Computing Simulation

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Java 17](https://img.shields.io/badge/Java-OpenJDK%2017-orange.svg)](https://openjdk.org/)
[![iFogSim2](https://img.shields.io/badge/Simulator-iFogSim2%20v2.0.0-green.svg)](https://github.com/Cloudslab/iFogSim)
[![Dataset](https://img.shields.io/badge/Dataset-UCI%20N--BaIoT-yellow.svg)](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot)
[![Tests](https://img.shields.io/badge/Tests-13%20Passed-brightgreen.svg)]()

> **🌐 Interactive Web Dashboard:** Open **[dashboard/index.html](file:///c:/Users/shubh/OneDrive/Desktop/Riddhi/dashboard/index.html)** in any web browser for a zero-dependency, standalone HTML/SVG simulation visualizer with live packet animation, 48-scenario sweep explorer, and 115-feature deep inspection!
> 
> **🎓 Interactive Faculty Viva Guide:** Open **[dashboard/viva_guide.html](file:///c:/Users/shubh/OneDrive/Desktop/Riddhi/dashboard/viva_guide.html)** for a dedicated web manual with defense Q&A cards, mathematical latency proofs, and cheat-sheet metrics.
> 
> **📖 Complete Project & Viva Guide (Markdown):** Read **[PROJECT_EXPLANATION.md](file:///c:/Users/shubh/OneDrive/Desktop/Riddhi/docs/PROJECT_EXPLANATION.md)**.

> **Project Purpose:** A reproducible, faculty-ready academic prototype combining machine learning with fog-computing simulation to answer two core questions:
> 1. **Detection:** Can supervised machine-learning models accurately identify benign vs. botnet-infected IoT traffic from high-dimensional network statistics?
> 2. **Placement:** Is it faster, more bandwidth-efficient, and more reliable to process security alerts locally at a Fog Gateway or in a centralized Remote Cloud Data Centre?

---

## 1. System Architecture

```text
IoT Devices (e.g. Smart Doorbells, Cameras, Thermostats)
    |
    | network traffic statistics (115 features per record)
    v
Fog Gateway
    |
    +--> Python ML Classifier (Random Forest / MLP baseline)
    |       |
    |       +--> BENIGN  ------------> ALLOW
    |       |
    |       +--> MALICIOUS / ATTACK -> QUARANTINE_RECOMMENDED
    |                                         |
    +--> iFogSim2 Simulation Engine:           v
             Process at Fog Gateway OR Remote Cloud Server
             Compare response time, WAN network traffic, and energy
```

---

## 2. Key Verified Empirical Results

### 2.1 Machine Learning Performance (Held-Out Test Set: 6,600 Unseen Records)

| Task | Selected Model | Accuracy | Macro Precision | Macro Recall | Macro-F1 Score | Inference Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Task A (Binary)** | **Random Forest** | **99.98%** | **100.00%** | **99.98%** | **99.99%** | **0.0066 ms / record** |
| **Task A (Binary Baseline)** | MLP (Dense 64+32) | 99.97% | 99.97% | 99.97% | 99.91% | 0.0051 ms / record |
| **Task B (11-Class Attack Family)** | **Random Forest** | **99.98%** | **99.98%** | **99.98%** | **99.98%** | **0.0074 ms / record** |
| **Task B (Multi-Class Baseline)** | MLP (Dense 64+32) | 90.71% | 90.85% | 90.71% | 87.70% | 0.0068 ms / record |

### 2.2 55-Record Demonstration Results
- **Total Records Evaluated:** 55
- **Predicted Benign (ALLOW):** 5 (100.0% agreement with ground-truth)
- **Predicted Malicious (QUARANTINE_RECOMMENDED):** 50 (100.0% agreement with ground-truth across 10 attack classes)

### 2.3 iFogSim2 Placement Simulation Results (10 IoT Devices, 100 ms WAN Link)

| Placement Location | Completed Records | Mean Latency | Median Latency | P95 Latency | WAN Network Traffic |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Local Fog Gateway** | **590** | **9.38 ms** | **9.38 ms** | **9.38 ms** | **0.00 KB (Zero WAN overhead)** |
| **Remote Cloud Server** | **590** | **206.98 ms** | **206.98 ms** | **206.98 ms** | **659.30 KB (675,120 bytes)** |
| **Fog Improvement** | — | **-95.5% Latency Reduction** | — | — | **-100% WAN Traffic Reduction** |

---

## 3. Repository Structure

```text
FogSentinel/
├── README.md                                    # Comprehensive setup and project guide
├── FogSentinel_Project_Understanding_and_...md # Full project blueprint specification
├── requirements.txt                             # Pinned Python package dependencies
├── pyproject.toml                               # Python project configuration
│
├── config/
│   ├── data.yaml                                # Dataset paths, class definitions, split ratios
│   ├── model.yaml                               # Model hyper-parameters, thresholds, actions
│   └── simulation.yaml                          # Simulation topologies, latencies, payloads
│
├── data/
│   ├── raw/                                     # Downloaded official UCI N-BaIoT files
│   ├── processed/                               # Scaled feature matrices (X_train, y_train, etc.)
│   └── demo/
│       ├── demo_features.csv                    # 55 x 115 input matrix (strictly NO labels)
│       └── demo_labels.csv                      # Separate ground-truth labels for verification
│
├── ml/
│   ├── data_loader.py                           # Chunked data ingestion & schema extraction
│   ├── preprocessing.py                         # Leakage-free StandardScaler pipeline
│   ├── model.py                                 # MLP, Random Forest, Logistic Regression
│   ├── train.py                                 # Multi-task training & validation selection
│   ├── evaluate.py                              # Held-out test evaluation & confusion matrices
│   ├── predict.py                               # 55-record inference service
│   └── explain.py                               # Top discriminative network features
│
├── artifacts/
│   ├── feature_schema.json                      # Canonical 115 feature columns
│   ├── scaler/standard_scaler.joblib            # Fitted StandardScaler
│   └── model/                                   # Trained model checkpoints
│
├── simulator/
│   ├── iFogSim/                                 # Official Cloudslab iFogSim2 repository (v2.0.0)
│   └── src/main/java/org/fogsentinel/
│       ├── TopologyBuilder.java                 # Cloud, Fog Gateway, and IoT Device topology
│       ├── ApplicationBuilder.java              # DDF application graph, tuples, and loops
│       ├── PlacementStrategy.java               # Strict Fog vs. Cloud module mappings
│       ├── MetricsCollector.java                # Latency, throughput, and WAN byte counters
│       ├── FogSentinelController.java           # Multi-scenario simulation controller
│       └── FogSentinelSimulation.java           # CLI runner (--quick and --sweep)
│
├── integration/
│   ├── export_workload.py                       # ML prediction to simulation bridge
│   ├── generate_simulation_figures.py           # Plotted simulation charts from real CSVs
│   └── run_pipeline.py                          # Single-command end-to-end pipeline runner
│
├── dashboard/
│   ├── index.html                               # Standalone interactive HTML simulation dashboard (Zero-dependency)
│   ├── viva_guide.html                          # Dedicated Faculty Viva Examination & Defense HTML Guide
│   ├── generate_html_dashboard.py               # HTML dashboard generator
│   └── app.py                                   # Interactive Streamlit faculty demo UI
│
├── outputs/
│   ├── model/                                   # Metrics CSVs, dataset summary, comparisons
│   ├── demo/                                    # demo_predictions.csv, workload_manifest.csv
│   ├── simulation/                              # quick_demo_results.csv, simulation_results.csv
│   └── figures/                                 # High-res publication charts
│
├── tests/
│   ├── test_data_schema.py                      # 115 features and demo shape tests
│   ├── test_preprocessing.py                    # Scaler transform and alignment tests
│   ├── test_prediction.py                       # Predictor output and action policy tests
│   └── test_simulation_results.py               # Verified simulation output tests
│
└── docs/
    ├── architecture.md                          # Detailed system topology and DDF specification
    ├── methodology.md                           # Mathematical formulation & preprocessing rules
    ├── viva_questions.md                        # Faculty viva examination questions & answers
    └── references.md                            # Academic citations and DOIs
```

---

## 4. Quick-Start Guide (Windows PowerShell / VS Code)

### 4.1 Activate Environment
```powershell
# Virtual environment is already configured in .venv
.\.venv\Scripts\activate
```

### 4.2 Run End-to-End Pipeline (One Command)
```powershell
# Executes data loading, preprocessing, training, evaluation, demo prediction, and Java simulation
python integration/run_pipeline.py
```

### 4.3 Open the Interactive Web Dashboard
You have two ways to view the interactive dashboard:

**Option A: Standalone Zero-Dependency HTML Dashboard (Instant in Browser)**
```powershell
Start-Process dashboard/index.html
# Or simply double-click dashboard/index.html in Windows File Explorer!
```

**Option B: Streamlit Web Dashboard**
```powershell
python -m streamlit run dashboard/app.py
```

### 4.4 Run Automated Test Suite
```powershell
python -m pytest tests/ -v
```

---

## 5. Individual Execution Commands

### Step 1: Ingest Dataset & Validate 115-Feature Schema
```powershell
python ml/data_loader.py
```

### Step 2: Fit Preprocessing Scaler
```powershell
python ml/preprocessing.py
```

### Step 3: Train & Select Models
```powershell
python ml/train.py
```

### Step 4: Evaluate on Held-Out Test Set
```powershell
python ml/evaluate.py
```

### Step 5: Run 55-Record Prediction Demo
```powershell
python ml/predict.py
```

### Step 6: Compile & Run Java iFogSim2 Simulation
```powershell
# Gather classpath jars
$jars = (Get-ChildItem -Recurse simulator/iFogSim/jars/*.jar | ForEach-Object { $_.FullName }) -join ";"
$cp = "simulator/iFogSim/bin;$jars"

# Compile FogSentinel simulation
javac -cp "$cp" -d simulator/iFogSim/bin (Get-ChildItem simulator/src/main/java/org/fogsentinel/*.java | ForEach-Object { $_.FullName })

# Run Quick Faculty Demo Mode (10 devices, 100 ms WAN delay)
java -cp "$cp" org.fogsentinel.FogSentinelSimulation --quick

# Run Full 48-Scenario Parameter Sweep
java -cp "$cp" org.fogsentinel.FogSentinelSimulation --sweep
```

### Step 7: Generate Simulation Analysis Visualizations
```powershell
python integration/generate_simulation_figures.py
```

---

## 6. Faculty Demonstration Script (4–6 Minutes)

1. **Step 1: Open the Dashboard (`streamlit run dashboard/app.py`):**
   - Show Tab 1: Point out that the demonstration evaluates **55 records**, each containing **115 continuous features**.
   - Click **Load & Classify 55 Demo Records**.
   - Show that exactly **5 ALLOW** and **50 QUARANTINE_RECOMMENDED** predictions are produced directly by the model.
   - Open the **Ground-Truth Verification** expander to prove 100% agreement on both binary detection and exact attack families.
2. **Step 2: Explain Feature Extraction (Tab 4):**
   - Point out that **jitter means** and **stream aggregation weights** are the top discriminative features distinguishing Mirai and BASHLITE.
3. **Step 3: Fog vs. Cloud Simulation Comparison (Tab 2):**
   - Show the live comparison cards: Fog response time is **9.38 ms**, Cloud response time is **206.98 ms**.
   - Explain why: The cloud incurs a **200 ms round-trip WAN link delay** (100 ms uplink + 100 ms downlink), while the Fog Gateway processes traffic locally over LAN.
   - Show the WAN bandwidth metric: Fog placement uses **0 KB WAN traffic**, saving 100% of Internet bandwidth compared to Cloud.
4. **Step 4: Academic Integrity & Limitations:**
   - State clearly that this is an academic prototype with simulated containment recommendations, not a physical hardware deployment.

---

## 7. Limitations & Ethical Disclosures

1. **Dataset Nature:** The study utilizes the public UCI N-BaIoT recorded dataset, not live traffic from arbitrary unstudied IoT hardware.
2. **Generalization:** High detection scores on known Mirai/BASHLITE variants do not guarantee equal performance against novel, unobserved zero-day exploits.
3. **Quarantine Recommendation:** The action `QUARANTINE_RECOMMENDED` is a simulated recommendation; no physical network interface was modified.
4. **Energy Model:** Energy consumption was calculated via a linear power model in iFogSim2; energy savings are not universally guaranteed in fog computing due to idle gateway power draw.

