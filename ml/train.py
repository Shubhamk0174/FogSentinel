import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from ml.model import build_model

def train_and_select_models():
    print("=========================================================================")
    print("           FogSentinel — Model Training & Selection Pipeline             ")
    print("=========================================================================")
    
    # 1. Load preprocessed features and targets
    X_train = np.load("data/processed/X_train.npy")
    X_val = np.load("data/processed/X_val.npy")
    
    y_train_df = pd.read_csv("data/processed/y_train.csv")
    y_val_df = pd.read_csv("data/processed/y_val.csv")
    
    y_train_bin = y_train_df["binary_label"].values
    y_val_bin = y_val_df["binary_label"].values
    
    y_train_multi = y_train_df["multi_label"].values
    y_val_multi = y_val_df["multi_label"].values
    
    tasks = [
        ("Binary", y_train_bin, y_val_bin, "artifacts/model/best_binary_model.joblib"),
        ("Multi-Class", y_train_multi, y_val_multi, "artifacts/model/best_multiclass_model.joblib")
    ]
    
    model_candidates = ["logistic_regression", "random_forest", "mlp"]
    validation_records = []
    
    artifacts_dir = Path("artifacts/model")
    outputs_dir = Path("outputs/model")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    for task_name, y_tr, y_va, best_save_path in tasks:
        print(f"\n--- Training Candidates for Task: {task_name} ---")
        best_val_f1 = -1.0
        best_model = None
        best_model_name = None
        
        for name in model_candidates:
            print(f"  Training {name.upper()}... ", end="", flush=True)
            model = build_model(name)
            
            t0 = time.time()
            model.fit(X_train, y_tr)
            train_duration = time.time() - t0
            
            # Predict on Validation
            preds = model.predict(X_val)
            acc = accuracy_score(y_va, preds)
            prec = precision_score(y_va, preds, average="macro", zero_division=0)
            rec = recall_score(y_va, preds, average="macro", zero_division=0)
            f1 = f1_score(y_va, preds, average="macro", zero_division=0)
            
            print(f"Done in {train_duration:.2f}s | Val Acc: {acc*100:.2f}% | Val Macro-F1: {f1*100:.2f}%")
            
            validation_records.append({
                "task": task_name,
                "model": name,
                "val_accuracy": acc,
                "val_precision_macro": prec,
                "val_recall_macro": rec,
                "val_macro_f1": f1,
                "training_time_sec": train_duration
            })
            
            if f1 > best_val_f1:
                best_val_f1 = f1
                best_model = model
                best_model_name = name
                
        print(f"\n[Selection] Best model for {task_name}: {best_model_name.upper()} (Validation Macro-F1: {best_val_f1*100:.2f}%)")
        joblib.dump(best_model, best_save_path)
        print(f"[Checkpoint] Saved {best_model_name} to {best_save_path}")
        
    df_val_results = pd.DataFrame(validation_records)
    val_csv = outputs_dir / "validation_results.csv"
    df_val_results.to_csv(val_csv, index=False)
    print(f"\n[Results] Validation summary saved to {val_csv}")
    
    return df_val_results

if __name__ == "__main__":
    train_and_select_models()
