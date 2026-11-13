import os
import sys
from pathlib import Path
import pandas as pd

def export_workload_manifest(predictions_csv="outputs/demo/demo_predictions.csv",
                             output_manifest="outputs/demo/workload_manifest.csv"):
    """
    Constructs the documented bridge between Python ML detection and iFogSim2 simulation:
    Reads prediction decisions and estimates processing workload parameters
    (MIPS, network bytes, quarantine priority) for simulation consumption.
    """
    if not os.path.exists(predictions_csv):
        raise FileNotFoundError(f"Predictions CSV not found at {predictions_csv}")
        
    df = pd.read_csv(predictions_csv)
    
    # 115 float64 features = 920 bytes
    df["input_nw_bytes"] = 920
    # Estimated MLP forward-pass instruction count
    df["cpu_mips"] = 1000
    # Alert dispatch payload
    df["alert_nw_bytes"] = 128
    
    # Quarantine priority flag: malicious traffic requires immediate low-latency mitigation
    df["mitigation_priority"] = [
        "IMMEDIATE_LOCAL" if row["action"] == "QUARANTINE_RECOMMENDED" else "STANDARD"
        for _, row in df.iterrows()
    ]
    
    # Optimal placement recommendation based on latency criticality
    df["optimal_placement"] = [
        "fog" if row["action"] == "QUARANTINE_RECOMMENDED" else "fog_or_cloud"
        for _, row in df.iterrows()
    ]
    
    Path(output_manifest).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_manifest, index=False)
    print(f"[Bridge] Exported {len(df)} workload records to: {output_manifest}")
    return df

if __name__ == "__main__":
    export_workload_manifest()

