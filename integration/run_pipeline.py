import os
import sys
import time
import subprocess
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ml.data_loader import prepare_dataset
from ml.preprocessing import run_preprocessing_pipeline
from ml.train import train_and_select_models
from ml.evaluate import run_evaluation
from ml.predict import run_demo_prediction
from ml.explain import explain_feature_importance
from integration.export_workload import export_workload_manifest
from integration.generate_simulation_figures import generate_simulation_figures

def run_java_simulation(mode="quick"):
    print(f"\n[Step 7/9] Running iFogSim2 Java Simulation (Mode: {mode.upper()})...")
    # Gather jar dependencies
    jars_dir = ROOT_DIR / "simulator" / "iFogSim" / "jars"
    jar_files = list(jars_dir.rglob("*.jar"))
    classpath_elements = [str(ROOT_DIR / "simulator" / "iFogSim" / "bin")] + [str(j) for j in jar_files]
    classpath = ";".join(classpath_elements) if os.name == "nt" else ":".join(classpath_elements)
    
    cmd = ["java", "-cp", classpath, "org.fogsentinel.FogSentinelSimulation"]
    if mode == "sweep":
        cmd.append("--sweep")
    else:
        cmd.append("--quick")
        
    print(f"Executing: {' '.join(cmd[:4])} ...")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        print("Java Simulation stderr:\n", res.stderr)
        raise RuntimeError(f"Java simulation failed with code {res.returncode}")
    print(res.stdout)
    print("Java Simulation completed successfully.")

def run_full_pipeline(mode="quick"):
    t_start = time.time()
    print("=========================================================================")
    print("           FogSentinel — End-to-End Automated Pipeline Runner            ")
    print(f"           Mode: {mode.upper()} (Simulation: {mode.upper()})            ")
    print("=========================================================================")

    # Step 1: Data Ingestion & Schema Extraction
    print("\n[Step 1/9] Ingesting UCI N-BaIoT dataset and extracting schema...")
    prepare_dataset()

    # Step 2: Preprocessing & Scaler Fitting
    print("\n[Step 2/9] Running feature preprocessing and fitting StandardScaler...")
    run_preprocessing_pipeline()

    # Step 3: Model Training & Selection
    print("\n[Step 3/9] Training baseline and neural network models across tasks...")
    train_and_select_models()

    # Step 4: Model Evaluation
    print("\n[Step 4/9] Evaluating models on held-out test set...")
    run_evaluation()

    # Step 5: Demo Prediction (55 Records)
    print("\n[Step 5/9] Running inference on 55-record demonstration dataset...")
    run_demo_prediction()

    # Step 6: Feature Explainability
    print("\n[Step 6/9] Computing feature importance & interpretability...")
    explain_feature_importance()

    # Step 7: Export Workload Manifest Bridge
    print("\n[Step 7/9] Exporting ML predictions to simulation workload manifest...")
    export_workload_manifest()

    # Step 8: Java Simulation
    run_java_simulation(mode=mode)

    # Step 9: Simulation Figures Generation
    print("\n[Step 9/9] Generating simulation visualization charts...")
    csv_to_plot = "outputs/simulation/simulation_results.csv" if (mode == "sweep" or Path("outputs/simulation/simulation_results.csv").exists()) else "outputs/simulation/quick_demo_results.csv"
    generate_simulation_figures(csv_path=csv_to_plot)

    total_time = time.time() - t_start
    print("\n=========================================================================")
    print(f"   FogSentinel Pipeline Executed Successfully in {total_time:.1f} seconds!    ")
    print("=========================================================================")

if __name__ == "__main__":
    mode_arg = "quick"
    if len(sys.argv) > 1 and sys.argv[1] in ["--sweep", "--full", "sweep", "full"]:
        mode_arg = "sweep"
    run_full_pipeline(mode=mode_arg)

