# FogSentinel iFogSim2 Simulator

This directory houses the Java simulation component of FogSentinel, built on the official [Cloudslab iFogSim2](https://github.com/Cloudslab/iFogSim) toolkit.

## Directory Structure
- `iFogSim/`: Official cloned repository of iFogSim2 (v2.0.0 official release) containing CloudSim and iFogSim core dependencies in `jars/`.
- `src/main/java/org/fogsentinel/`: Custom FogSentinel simulation classes:
  - `TopologyBuilder.java`: Constructs Cloud Server, Fog Gateway, and IoT Devices with configurable WAN latency and LAN connectivity.
  - `ApplicationBuilder.java`: Defines the DDF application graph with `IOT_TRAFFIC` and `SECURITY_ALERT` edges and loops.
  - `PlacementStrategy.java`: Sets up strict Fog-Side vs. Cloud-Side execution mapping.
  - `MetricsCollector.java`: Extracts latency (mean, median, p95), completion rates, energy consumption, and explicit WAN traffic.
  - `FogSentinelController.java`: Custom controller supporting graceful termination without `System.exit(0)` for batch experimentation.
  - `FogSentinelSimulation.java`: Command-line runner supporting `--quick` (faculty demo) and `--sweep` (48-scenario parameter sweep).

## Standalone Compilation (PowerShell)
```powershell
$jars = (Get-ChildItem -Recurse simulator/iFogSim/jars/*.jar | ForEach-Object { $_.FullName }) -join ";"
$cp = "simulator/iFogSim/bin;$jars"

javac -cp "$cp" -d simulator/iFogSim/bin (Get-ChildItem simulator/src/main/java/org/fogsentinel/*.java | ForEach-Object { $_.FullName })
```

## Running Simulations
```powershell
# Quick Demo (10 devices, 100 ms WAN latency, 60s active run)
java -cp "$cp" org.fogsentinel.FogSentinelSimulation --quick

# Full 48-Scenario Sweep
java -cp "$cp" org.fogsentinel.FogSentinelSimulation --sweep
```

