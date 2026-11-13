# FogSentinel — Project Understanding and Implementation Blueprint

> **Purpose of this document:** Give a coding agent enough context to build a complete, reproducible, faculty-ready FogSentinel project. Treat this file as the project specification. Do not invent experiment results, claim hardware deployment, or describe a simulated action as a real security action.

---

## 1. Project overview

**FogSentinel** is an IoT network-traffic monitoring and attack-detection prototype that combines machine learning with fog-computing simulation.

The project answers two related questions:

1. **Detection:** Can a machine-learning model identify normal and malicious IoT traffic from statistical network features?
2. **Placement:** If an alert must be generated, is it faster to process the traffic near the IoT devices (at a fog gateway) or send it to a remote cloud server?

The project has two main technical components:

- A **Python machine-learning pipeline** that loads the N-BaIoT dataset, preprocesses traffic records, trains a classifier, evaluates it, and predicts whether a record is benign or malicious (and optionally which attack class it belongs to).
- A **Java simulation using iFogSim2** that models IoT devices, a fog gateway, and a cloud data centre. It compares fog-side and cloud-side processing under controlled network conditions.

The intended end-to-end concept is:

```text
IoT devices
    |
    | network traffic statistics (115 features per record)
    v
Fog gateway
    |
    +--> Python ML classifier
    |       |
    |       +--> BENIGN
    |       |
    |       +--> MALICIOUS / suspicious
    |                    |
    |                    v
    |              Alert / quarantine recommendation
    |
    +--> iFogSim2 experiment:
             process at fog gateway OR remote cloud
             compare response time, network usage and energy model
```

**Important distinction:** the Python classifier and iFogSim2 simulator are separate programs unless the implementation explicitly connects them. A proper final build should connect them through a documented interface or a shared experiment input file. Do not claim that iFogSim2 itself trains or runs the neural network. iFogSim2 models the computing/network environment and its timing/resource behaviour.

---

## 2. Problem statement and motivation

IoT devices such as smart cameras, doorbells, baby monitors and thermostats communicate over networks. If a device is compromised by a botnet, it may generate unusual traffic or participate in attacks such as scanning, flooding or command-and-control activity.

A cloud-only security design sends data to a remote data centre for analysis. This can introduce network delay and dependence on internet connectivity. A fog-computing design places some processing close to the IoT devices, for example on a local gateway. This can reduce the time required to make a decision and reduce the amount of raw traffic sent to the cloud.

FogSentinel explores both parts:

- Use statistical traffic features and a supervised ML model to identify suspicious traffic.
- Use a controlled fog-versus-cloud simulation to study the effect of processing location.

This is an academic prototype, not a production intrusion-prevention appliance. It does not inspect live packets or actually disconnect devices unless a separate real-network integration is implemented and tested.

---

## 3. Dataset

### 3.1 N-BaIoT

Use the **N-BaIoT (Network-Based Detection of IoT Botnet Attacks)** dataset from the UCI Machine Learning Repository:

- Dataset page: https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot
- DOI: `10.24432/C5RC8J`
- Dataset paper: Yair Meidan et al., *N-BaIoT—Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders*, 2018.
- Licence listed by UCI: CC BY 4.0.
- UCI describes 9 commercial IoT devices, 7,062,606 instances and 115 continuous features.
- The labels comprise benign traffic and 10 attack classes associated with Mirai and BASHLITE (the dataset filenames commonly use `gafgyt` for BASHLITE attack labels).

### 3.2 What is one record?

A record is one row of derived traffic statistics. It is **not** one complete packet, one device, or one whole attack.

Each record contains **115 numerical features**. These summarise network-stream behaviour over different aggregation scopes and time windows. Examples include statistics related to packet/stream sizes, timing, means, standard deviations, jitter, covariance and correlation.

Explain the dimensions correctly:

- **55 records** = 55 rows/examples selected for the small interactive demo.
- **115 features** = 115 input measurements/columns describing each row.
- Therefore, the demo input matrix has shape **55 × 115** (55 examples, each represented by 115 values), excluding any label column.

Do not say that the model only uses 55 features. It uses 115 features for each record.

### 3.3 Dataset preparation requirements

The coding agent must:

1. Download or allow the user to place the official dataset files under `data/raw/`.
2. Preserve the original files and document their source.
3. Parse labels from the source file names/folder structure or an explicit metadata manifest. Do not guess labels from row order.
4. Standardise column names consistently.
5. Verify that every feature row has exactly 115 numeric values.
6. Check for missing values, infinities, duplicate rows and malformed records.
7. Record the number of rows read from every source file.
8. Save a manifest with device, class label, source filename, row count and split assignment.
9. Avoid loading the entire 1.7 GB dataset into RAM if unnecessary; use chunked CSV reading or sampled training data.
10. Keep the 55-row demo subset separate from training and test datasets.

### 3.4 Avoid data leakage

A credible evaluation must not randomly mix highly correlated adjacent traffic rows between training and testing without considering their source. Use a documented split strategy.

Recommended options:

- **Within-device evaluation:** chronological or grouped train/validation/test split for each device.
- **Cross-device evaluation:** train on selected devices and test on a held-out device to examine generalisation.
- Fit scalers only on the training set, then apply the saved scaler to validation, test and demo data.

The final report must state exactly which split strategy was used. If device IDs or time order are unavailable for a particular subset, state that limitation.

---

## 4. Machine-learning component

### 4.1 Task definition

Support two classification tasks:

**Task A — Binary classification**
- `benign`
- `malicious`

This is useful for a simple security decision: allow normal-looking traffic or raise an alert.

**Task B — Multi-class classification**
- `benign`
- The 10 attack subtypes represented in the selected dataset files.

This task is harder because the model must identify the specific attack family, not merely detect that traffic is malicious.

The application should clearly show which task a displayed metric belongs to. Do not compare binary accuracy with multi-class accuracy as if they measured the same task.

### 4.2 Recommended model

Implement a reproducible feed-forward neural network (MLP) baseline in Python using PyTorch or scikit-learn. If reproducing the earlier prototype, use an MLP with two hidden layers (for example, 64 and 32 units), ReLU activations and a final classification layer. The exact architecture must be recorded in a configuration file.

Suggested structure:

```text
Input: 115 features
    |
Dense(64) + ReLU
    |
Dense(32) + ReLU
    |
Output layer: 2 units (binary) or 11 units (multi-class)
    |
Softmax / class probabilities
```

The model is trained using labelled examples. At inference time it receives only the 115 feature values and returns a predicted class and confidence/probability values.

### 4.3 Preprocessing

Implement and save a fitted preprocessing pipeline:

1. Read the 115 numeric features.
2. Validate feature order against a saved schema.
3. Handle missing/infinite values using a documented strategy.
4. Apply a suitable transformation if the feature distribution is highly skewed (for example, `log1p` only for non-negative features, where justified).
5. Fit a `StandardScaler` or other selected scaler using **training data only**.
6. Apply the same fitted transform to validation/test/demo/inference records.
7. Save the scaler and feature schema beside the trained model.

The inference code must reject files with missing, extra or reordered feature columns unless a safe, explicit column reordering can be performed using the saved feature names.

### 4.4 Training and model selection

Implement:

- Fixed random seeds.
- Train/validation/test separation.
- Model checkpointing based on validation macro-F1 or another predeclared metric.
- Early stopping where appropriate.
- Class weighting or a sampling strategy if class imbalance is substantial.
- A training history CSV and loss/metric plots.
- A saved configuration file containing dataset paths, feature list, labels, architecture, seed, split method and hyperparameters.

Compare a small set of models fairly, for example:
- Logistic Regression (baseline)
- Random Forest (baseline)
- MLP (proposed model)

Do not claim the neural network is best unless the same evaluation split and metrics show that.

### 4.5 Evaluation

Report at least:

- Accuracy
- Precision
- Recall
- Macro-F1
- Per-class precision/recall/F1
- Confusion matrix
- Training and inference time

For the binary task, pay particular attention to false negatives (malicious traffic predicted as benign) and false positives (benign traffic flagged as malicious).

For multi-class classification, macro-F1 is important because it gives each class equal weight, rather than allowing large classes to dominate the score.

### 4.6 Prediction and decision policy

The prediction service should return structured output such as:

```json
{
  "prediction": "malicious",
  "predicted_class": "mirai.scan",
  "confidence": 0.94,
  "action": "QUARANTINE_RECOMMENDED"
}
```

The exact class names and confidence values must come from the model output. The example above is illustrative only.

For the demo, use a clear threshold/policy:
- `benign` → `ALLOW`
- `malicious` → `QUARANTINE_RECOMMENDED`

Use the phrase **“quarantine recommended”** or **“quarantine simulated”**. Do not imply that the software has really blocked a device.

### 4.7 The 55-record demonstration

Create a small, reproducible CSV containing 55 selected rows and 115 features per row:

- `data/demo/demo_features.csv` — 55 × 115 input values.
- `data/demo/demo_labels.csv` — ground-truth labels, stored separately and not passed into the prediction function.
- `outputs/demo/demo_predictions.csv` — one prediction per input row, including predicted label, confidence and recommended action.

The user-facing demo should show:
- Total records processed: 55
- Number predicted benign
- Number predicted malicious
- A table with row number, predicted class, confidence and recommended action
- Optional ground-truth comparison in a separate evaluation view

**Do not hardcode “5 ALLOW and 50 QUARANTINE”.** That count was reported for an earlier demo run and must be regenerated from the actual model and actual demo CSV. It may change if the model, sample or preprocessing changes.

---

## 5. Fog computing and cloud computing

### 5.1 Basic concepts

**Cloud computing:** processing is performed at a remote data centre. IoT data travels through the network to the cloud, is processed there, and the result travels back.

**Fog computing:** processing is moved closer to the IoT devices, for example to a local gateway/router. This can reduce network round-trip delay and reduce dependence on the remote cloud.

**Edge device:** the IoT endpoint itself, such as a camera or doorbell.

**Fog node/gateway:** an intermediate compute node close to the devices.

**Cloud node:** a remote, more powerful compute resource.

### 5.2 Intended topology

```text
                +----------------------+
                |      Cloud Server    |
                |  classifier service  |
                +----------------------+
                         ^
                         | WAN link
                         |
+-----------+     +--------------------+
| IoT Device|---->| Fog Gateway        |
+-----------+     | local processing   |
                  | / forwarding       |
+-----------+     +--------------------+
| IoT Device|---->          |
+-----------+                |
                             v
                      Alert / Actuator
```

In the **fog scenario**, the processing module is placed on the fog gateway. In the **cloud scenario**, the same logical processing module is placed on the cloud server. All other workload and network assumptions should remain identical for a fair comparison.

### 5.3 What iFogSim2 does

Use the official iFogSim2 project:

- Repository: https://github.com/Cloudslab/iFogSim
- Its README describes it as a toolkit for modelling and simulating IoT, edge and fog environments. It extends iFogSim with mobility support, microservice management and dynamic clustering.
- iFogSim2 is a simulator. It does not automatically train the Python model or inspect live network packets.

Use iFogSim2's Java/CloudSim entities and APIs to model:
- IoT sensors/devices generating events or tuples.
- A fog gateway with defined CPU, RAM, storage, bandwidth and power parameters.
- A cloud data centre with defined resources.
- Network links with latency and bandwidth.
- Application modules representing feature processing/classification/alert generation.
- An actuator or response endpoint.
- A controller that starts and monitors the simulation.

Use the API/classes present in the checked-out iFogSim2 version. Do not copy class or method names from an unrelated older version without compiling against the actual repository.

### 5.4 Model the same workload in both placements

For a fair experiment:

- Keep the number of IoT devices identical.
- Keep the tuple/record generation rate identical.
- Keep module instruction length and resource requirements identical.
- Keep the network topology and WAN latency identical.
- Change only the processing placement (fog vs cloud).
- Ensure every generated record has a matching completed response, or report dropped/unfinished records.
- Drain pending events/queues before computing final averages.

### 5.5 Simulation parameters

The earlier prototype described a parameter sweep with:

- Device counts: 10, 50, 100, 200 (4 values)
- Traffic rates: 1 and 5 records per second per device (2 values)
- Cloud one-way latency: 25, 100, 200 ms (3 values)
- Processing placements: fog and cloud (2 values)

This produces:

`4 × 2 × 3 × 2 = 48` simulation configurations.

The earlier quick demonstration used:
- 10 devices
- 1 record per second per device
- 100 ms one-way cloud link latency
- Fog and cloud placement runs

An earlier run was reported as completing 591 responses in each placement, with average response times around 9.07 ms for fog and 212.13 ms for cloud. Treat these as **previously reported prototype values, not guaranteed outputs**. Re-run the final checked-in simulator and use the fresh CSV/console output in the final report. The exact 591 count should be explained from the simulator's event timing and run duration; do not claim it is exactly 600 unless the simulation actually emits 600 tuples.

### 5.6 Metrics to collect

At minimum:
- Mean end-to-end response time (ms)
- Median and 95th percentile response time (ms)
- Number of generated records
- Number of completed responses
- Number of dropped or unfinished records
- Network usage/bytes sent over the WAN (explicitly instrument this if the framework metric is not a byte count)
- CPU utilisation or processing cost, where available
- Energy consumption using a clearly documented power model, if supported

**Important:** Do not label a generic iFogSim network-usage metric as bytes unless it is actually measured in bytes. Add explicit byte counters for payloads crossing the WAN if reporting WAN traffic.

Energy results depend on the configured power model. Do not claim that fog always saves energy. The earlier prototype noted that fog did not consistently reduce modelled energy.

### 5.7 How the Python ML model and iFogSim2 should connect

For a strong, understandable implementation, use a documented bridge:

1. Python trains the model and saves the model plus scaler and feature schema.
2. Python runs inference on the demo/test CSV and writes a compact event file with record ID, predicted class, confidence, recommended action and an estimated processing workload.
3. The Java iFogSim2 application reads this event/workload file (or receives an equivalent generated workload) and simulates where the classification/alert processing is placed.
4. The simulator writes one CSV row per scenario and placement.
5. A Python analysis script combines model metrics and simulation metrics into charts and a summary report.

If the simulator only models a generic classification workload rather than invoking the trained Python model, state that clearly. It is valid to simulate the compute/network placement of a classifier without embedding Python inside Java, but do not claim that iFogSim2 executed the neural network.

---

## 6. Recommended software architecture

Use a clean repository layout:

```text
FogSentinel/
├── README.md
├── PROJECT_SPEC.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── config/
│   ├── data.yaml
│   ├── model.yaml
│   └── simulation.yaml
│
├── data/
│   ├── raw/                 # original UCI data; do not commit large files
│   ├── processed/
│   └── demo/
│       ├── demo_features.csv
│       └── demo_labels.csv
│
├── ml/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── train.py
│   ├── evaluate.py
│   ├── predict.py
│   ├── model.py
│   └── explain.py
│
├── artifacts/
│   ├── model/
│   ├── scaler/
│   └── feature_schema.json
│
├── simulator/
│   ├── README.md
│   ├── pom.xml or build configuration supported by the chosen iFogSim2 setup
│   └── src/main/java/
│       └── org/fogsentinel/
│           ├── FogSentinelSimulation.java
│           ├── TopologyBuilder.java
│           ├── ApplicationBuilder.java
│           ├── WorkloadGenerator.java
│           ├── PlacementStrategy.java
│           └── MetricsCollector.java
│
├── integration/
│   ├── export_workload.py
│   └── run_pipeline.py
│
├── dashboard/
│   └── app.py               # optional Streamlit demo
│
├── outputs/
│   ├── model/
│   ├── demo/
│   ├── simulation/
│   └── figures/
│
├── tests/
│   ├── test_data_schema.py
│   ├── test_preprocessing.py
│   ├── test_prediction.py
│   └── test_simulation_results.py
│
└── docs/
    ├── architecture.md
    ├── methodology.md
    ├── viva_questions.md
    └── references.md
```

The agent may adapt the exact layout to the iFogSim2 build system, but keep Python ML code and Java simulation code clearly separated.

---

## 7. Suggested implementation workflow

Build the project in the following order. Each phase must finish with a test or visible output before moving on.

### Phase 1 — Repository and environment

1. Create the repository and directory structure.
2. Set up Python 3.10+ (choose a version compatible with the ML libraries).
3. Set up a JDK compatible with the checked-out iFogSim2/CloudSim version. Verify the version from the official repository and compile a sample before implementing the custom simulation.
4. Clone the official iFogSim2 repository or use it as a pinned dependency/submodule.
5. Record exact Python, Java, iFogSim2 and CloudSim versions.
6. Add reproducible setup instructions for Windows PowerShell and Linux/macOS.

Acceptance check:
- `python --version`
- `java -version`
- A stock iFogSim2 example compiles and runs before custom code is written.

### Phase 2 — Dataset ingestion

1. Download the official N-BaIoT dataset from UCI.
2. Extract the relevant device CSV files.
3. Implement a chunked loader and label parser.
4. Validate 115 feature columns.
5. Produce a dataset summary CSV and label distribution chart.
6. Save a deterministic 55-row demo sample with its feature schema.

Acceptance check:
- Print dataset dimensions and class counts.
- Confirm the demo features file has 55 rows and 115 feature columns.
- Confirm the labels are stored separately from model inputs.

### Phase 3 — Preprocessing and model training

1. Implement preprocessing.
2. Create leakage-aware train/validation/test splits.
3. Train simple baselines.
4. Train the MLP.
5. Select the model using validation macro-F1.
6. Evaluate once on the held-out test set.
7. Save model, scaler, schema, configuration, metrics and plots.

Acceptance check:
- Training completes from a clean environment.
- A saved model can be loaded in a separate Python process.
- Evaluation produces accuracy, precision, recall, macro-F1 and a confusion matrix.
- Repeating with the same seed produces materially consistent results.

### Phase 4 — Prediction demo

1. Load the saved model and scaler.
2. Read the 55-row demo feature CSV.
3. Validate feature names and ordering.
4. Predict one output per row.
5. Save `demo_predictions.csv`.
6. Build a simple Streamlit interface with upload/run controls and a results table.
7. Show benign/malicious counts computed from the actual predictions.

Acceptance check:
- Exactly 55 predictions are produced for 55 valid input rows.
- Invalid input shape or missing features causes a clear error.
- The UI does not use hardcoded prediction totals.

### Phase 5 — iFogSim2 simulation

1. Clone and build official iFogSim2.
2. Run an official example to verify dependencies.
3. Implement the IoT devices, fog gateway, cloud server, network links, application modules and actuator/response path.
4. Implement fog and cloud placement as two explicit configurations.
5. Use identical workload and resource settings in both configurations.
6. Collect per-record response times and completion counts.
7. Add explicit WAN byte counters if reporting network bytes.
8. Implement the 48-case parameter sweep.
9. Save raw results as CSV and create plots.

Acceptance check:
- Both fog and cloud configurations compile and run.
- The run log records all simulation parameters.
- Each scenario has generated/completed/dropped counts.
- Every plotted value can be traced to a CSV result row.
- A quick mode completes quickly for a live faculty demo.

### Phase 6 — Integration

1. Export the Python demo predictions or a generated workload manifest.
2. Read the manifest from the Java simulation or use it to configure tuple generation.
3. Use the same event count/workload for fog and cloud.
4. Store the prediction ID/class and simulation response time together where practical.
5. Clearly document whether the simulator models actual model inference or only the compute workload of a classifier.

Acceptance check:
- One command runs the pipeline from prediction export through simulation.
- Output files contain a run ID, model version, scenario configuration and timestamp.
- No metric is manually typed into a report or dashboard.

### Phase 7 — Analysis and presentation

Generate automatically from result files:
- Model comparison table
- Confusion matrix
- Per-class metric chart
- Fog-vs-cloud latency chart
- Latency versus device-count chart
- WAN traffic comparison
- Energy comparison (only if measured with a documented model)
- A concise summary table

Prepare:
- README with exact setup/run commands
- Architecture diagram
- Methodology and experiment settings
- Limitations and future work
- Faculty demo script and viva questions

Acceptance check:
- Delete generated outputs and rerun the pipeline; all figures and tables regenerate.
- Report numbers match the raw CSV files.
- No placeholder, fabricated or stale values remain.

---

## 8. Demo plan for faculty

A short but convincing demonstration should take 4–6 minutes.

### Demo A — ML-based traffic detection

1. Open the dashboard or run the prediction script.
2. Load the 55-row demo dataset.
3. Show that each row contains 115 features.
4. Click **Run classifier**.
5. Show the prediction table and the actual benign/malicious counts.
6. Open one row and explain: 115 statistical values go into the model; the model returns a predicted label and confidence.
7. Explain that the 55-row set is a small demonstration sample, not the full training dataset.

### Demo B — Fog versus cloud simulation

1. Open the Java iFogSim2 project in VS Code/IDE.
2. Open the topology/application configuration.
3. Point out the IoT devices, fog gateway and cloud data centre.
4. Show the two placement configurations: fog and cloud.
5. Run the quick simulation.
6. Show the generated CSV and latency comparison chart.
7. Explain the configured one-way WAN delay and why cloud round-trip communication increases response time.
8. State clearly that this is a simulation, not a physical network deployment.

### Demo C — End-to-end explanation

Explain the data flow:

- N-BaIoT provides labelled traffic examples.
- Python preprocessing converts each record into a consistent 115-feature vector.
- The trained model classifies the record.
- The system produces an alert/quarantine recommendation.
- iFogSim2 compares the response path when processing is placed at a local fog gateway or in the remote cloud.
- The results help evaluate the trade-off between response time, network traffic and resource/energy use.

---

## 9. Previously reported prototype results — verify before reuse

The earlier working notes in this project conversation mentioned the following values. They are **historical prototype results** and must not be treated as fresh results until the final source code is rerun and the output files confirm them.

### Machine-learning results previously mentioned

- 11-class classification accuracy: approximately **75.70%** in one reported run.
- A separate unseen-device evaluation (training on two devices and testing on a baby monitor) was reported at approximately **81.0%**.
- Binary benign-versus-malicious accuracy on a doorbell test was reported at approximately **99.98%**.
- The binary result was described as catching 20,000 attack records and incorrectly flagging 4 of 2,000 benign records.
- A separate 55-record demo was reported as 5 `ALLOW` and 50 `QUARANTINE`.

These values refer to different experiments and must not be mixed. The coding agent must inspect the raw metrics, split definitions and confusion matrices before placing them in a final report. If the raw files are unavailable, rerun the experiments and replace the values.

### iFogSim2 results previously mentioned

A quick simulation was reported with:
- 10 IoT devices
- 1 record/second/device
- 100 ms one-way cloud link delay
- 591 completed responses per placement
- Fog average response time: approximately **9.07 ms**
- Cloud average response time: approximately **212.13 ms**

The full parameter sweep was described as 48 configurations:
`4 device counts × 2 traffic rates × 3 WAN delays × 2 placements`.

The earlier notes also said fog did **not** consistently reduce modelled energy. Preserve this caveat.

**Do not hardcode these numbers into source code.** The final report and dashboard must read measured values from fresh output files.

---

## 10. Limitations to acknowledge

1. The project uses a public dataset of recorded traffic, not live traffic from the user's own IoT devices.
2. Dataset-based classification performance does not guarantee detection of new malware or attacks absent from the training data.
3. A high binary score does not imply equally high exact attack-family classification.
4. The 55-row demo is for quick presentation; it is not statistically sufficient for a performance claim.
5. iFogSim2 results depend on the simulated topology, resource allocation, workload, network latency and power model.
6. A simulation does not prove that a real gateway can achieve the same latency.
7. A quarantine recommendation is not actual network isolation unless a real enforcement integration is implemented.
8. The model may produce false positives and false negatives; a production system would need threshold tuning, monitoring and safe fallback behaviour.
9. Energy savings are not guaranteed. Report the configured power model and measured results.
10. The project should not be described as a fully deployed IDS/IPS unless live packet capture, inference and enforcement are implemented and tested.

---

## 11. Improvements that make the project stronger

Prioritise the following improvements:

- **Reproducibility:** one command to prepare data, train, evaluate, predict and run simulation.
- **Clear architecture:** separate ML inference from simulation, with a documented integration bridge.
- **Model transparency:** show confusion matrix, class-wise metrics and prediction confidence.
- **Fair comparison:** same workload and resource assumptions for fog and cloud.
- **Useful measurements:** mean, median, p95 latency, completion rate and explicit WAN bytes.
- **A polished demo:** Streamlit dashboard with traffic predictions and simulation comparison.
- **Experiment tracking:** every result includes configuration, random seed, model version and timestamp.
- **Robustness:** test invalid CSVs, missing columns, class imbalance and model-loading failures.
- **Security framing:** describe actions as recommendations unless real network enforcement exists.

Optional future work:
- Deploy the model to a Raspberry Pi or other constrained gateway.
- Capture live traffic using a controlled test network.
- Add a safe network enforcement mechanism.
- Evaluate concept drift and previously unseen attack types.
- Compare multiple fog placement strategies.
- Explore dynamic placement based on network congestion and device load.

---

## 12. Instructions to the AI coding agent

Build the project, do not merely write a plan.

### Required behaviour

1. First inspect the existing repository and preserve useful working code.
2. Verify all existing files and dependencies before replacing anything.
3. Use the official UCI N-BaIoT dataset and official Cloudslab iFogSim2 repository.
4. Pin versions and record the exact environment.
5. Implement Python ML and Java simulation as separate, testable components.
6. Create a documented interface between prediction output and simulation workload.
7. Implement a small quick-run mode and a full experiment mode.
8. Add unit tests and integration tests.
9. Run the tests and fix errors before claiming completion.
10. Generate all tables and charts from raw output files.
11. Include exact Windows PowerShell commands for VS Code users.
12. Keep large raw dataset files and generated model binaries out of Git; document how to obtain them.
13. Never invent output values, pretend a command ran, or label a placeholder as a measured result.
14. If a required dependency cannot be installed or compiled, explain the blocker and provide the exact failing command/log.

### Definition of done

The project is complete only when:

- A clean setup can install dependencies.
- Dataset validation confirms the 115-feature schema.
- Training and evaluation run and save real metrics.
- The 55-row demo produces 55 predictions from the saved model.
- iFogSim2 compiles and runs both fog and cloud scenarios.
- The 48-case experiment can be reproduced.
- Raw CSVs, charts and summary tables are generated.
- A single quick demo command works.
- README instructions are accurate and tested.
- The report distinguishes measured results, simulation assumptions and limitations.

---

## 13. References

1. UCI Machine Learning Repository, **Detection of IoT Botnet Attacks (N-BaIoT)**, https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot, DOI: 10.24432/C5RC8J.
2. Meidan, Y. et al. (2018), **N-BaIoT—Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders**, IEEE Pervasive Computing.
3. Cloudslab, **iFogSim / iFogSim2 source repository and README**, https://github.com/Cloudslab/iFogSim.
4. Mahmud, R., Pallewatta, S., Goudarzi, M., and Buyya, R. (2022), **iFogSim2: An Extended iFogSim Simulator for Mobility, Clustering, and Microservice Management in Edge and Fog Computing Environments**, Journal of Systems and Software, 190.

---

## 14. One-minute project explanation

“FogSentinel is an IoT security prototype that combines machine learning with fog-computing simulation. I use the N-BaIoT dataset, which contains traffic records from real IoT devices affected by Mirai and BASHLITE botnets. Each record has 115 statistical network features. A Python neural network learns patterns from labelled examples and predicts whether a new record looks benign or malicious.

The second part uses iFogSim2, a Java-based simulator, to model IoT devices, a nearby fog gateway and a remote cloud server. I run the same workload with processing placed at the gateway and then at the cloud. I compare response time and other resource/network metrics. The goal is to understand whether moving security analysis closer to IoT devices can reduce response delay. The current project is a dataset-based prototype and simulation; it does not claim to block real devices.”
