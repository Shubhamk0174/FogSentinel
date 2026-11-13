import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import joblib
import pandas as pd
import numpy as np

os.environ["MPLCONFIGDIR"] = str(Path(".cache/matplotlib").resolve())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def explain_feature_importance():
    print("=========================================================================")
    print("        FogSentinel — Feature Importance & Network Interpretability      ")
    print("=========================================================================")
    
    with open("artifacts/feature_schema.json", "r") as f:
        schema = json.load(f)
    feature_names = schema["features"]
    
    model = joblib.load("artifacts/model/best_binary_model.joblib")
    
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        print("Model does not provide direct feature weights.")
        return
        
    df_imp = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)
    
    outputs_dir = Path("outputs/model")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    df_imp.to_csv(outputs_dir / "feature_importance.csv", index=False)
    print(f"Top 10 Most Discriminative Network Features:")
    for idx, row in df_imp.head(10).iterrows():
        print(f"  {idx+1:2d}. {row['feature']:25s} | Importance: {row['importance']:.6f}")
        
    # Plot top 15 features
    top15 = df_imp.head(15).iloc[::-1]
    plt.figure(figsize=(10, 6))
    plt.barh(top15["feature"], top15["importance"], color="teal", edgecolor="black")
    plt.title("FogSentinel — Top 15 Discriminative Network Features (N-BaIoT)", fontsize=12, pad=12)
    plt.xlabel("Importance Score", fontsize=10)
    plt.tight_layout()
    chart_path = Path("outputs/figures/top_features.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"[Figure] Saved top features chart to {chart_path}")
    
    return df_imp

if __name__ == "__main__":
    explain_feature_importance()

