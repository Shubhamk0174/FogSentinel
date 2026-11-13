import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

os.environ["MPLCONFIGDIR"] = str(Path(".cache/matplotlib").resolve())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_confusion_matrix(cm, class_names, title, save_path):
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title(title, fontsize=14, pad=15)
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha="right", fontsize=9)
    plt.yticks(tick_marks, class_names, fontsize=9)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            text = f"{val}" if val < 10000 else f"{val/1000:.1f}k"
            plt.text(j, i, text,
                     horizontalalignment="center",
                     verticalalignment="center",
                     color="white" if val > thresh else "black",
                     fontsize=8)

    plt.ylabel("True Label", fontsize=11)
    plt.xlabel("Predicted Label", fontsize=11)
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[Figure] Confusion matrix saved to {save_path}")

def run_evaluation():
    print("=========================================================================")
    print("          FogSentinel — Held-Out Test Set Comprehensive Evaluation       ")
    print("=========================================================================")

    X_test = np.load("data/processed/X_test.npy")
    y_test_df = pd.read_csv("data/processed/y_test.csv")
    y_test_bin = y_test_df["binary_label"].values
    y_test_multi = y_test_df["multi_label"].values

    outputs_dir = Path("outputs/model")
    figures_dir = Path("outputs/figures")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Evaluate Binary Model
    bin_model_path = "artifacts/model/best_binary_model.joblib"
    bin_model = joblib.load(bin_model_path)
    
    t0 = time.time()
    y_pred_bin = bin_model.predict(X_test)
    bin_infer_time = (time.time() - t0) * 1000.0 / len(X_test)

    bin_acc = accuracy_score(y_test_bin, y_pred_bin)
    bin_prec = precision_score(y_test_bin, y_pred_bin, pos_label="malicious", zero_division=0)
    bin_rec = recall_score(y_test_bin, y_pred_bin, pos_label="malicious", zero_division=0)
    bin_f1 = f1_score(y_test_bin, y_pred_bin, pos_label="malicious", zero_division=0)

    print("\n--- [Task A: Binary Classification Results (Held-Out Test Set)] ---")
    print(f"Total Test Records: {len(X_test):,}")
    print(f"Accuracy:           {bin_acc * 100:.2f}%")
    print(f"Precision:          {bin_prec * 100:.2f}%")
    print(f"Recall:             {bin_rec * 100:.2f}%")
    print(f"F1 Score:           {bin_f1 * 100:.2f}%")
    print(f"Inference Latency:  {bin_infer_time:.4f} ms/record")

    bin_classes = ["benign", "malicious"]
    cm_bin = confusion_matrix(y_test_bin, y_pred_bin, labels=bin_classes)
    plot_confusion_matrix(cm_bin, bin_classes, "Binary Classification Confusion Matrix", figures_dir / "confusion_matrix_binary.png")

    # 2. Evaluate Multi-Class Model
    multi_model_path = "artifacts/model/best_multiclass_model.joblib"
    multi_model = joblib.load(multi_model_path)

    t0 = time.time()
    y_pred_multi = multi_model.predict(X_test)
    multi_infer_time = (time.time() - t0) * 1000.0 / len(X_test)

    multi_acc = accuracy_score(y_test_multi, y_pred_multi)
    multi_prec_macro = precision_score(y_test_multi, y_pred_multi, average="macro", zero_division=0)
    multi_rec_macro = recall_score(y_test_multi, y_pred_multi, average="macro", zero_division=0)
    multi_f1_macro = f1_score(y_test_multi, y_pred_multi, average="macro", zero_division=0)

    print("\n--- [Task B: Multi-Class Classification Results (11 Classes)] ---")
    print(f"Total Test Records: {len(X_test):,}")
    print(f"Accuracy:           {multi_acc * 100:.2f}%")
    print(f"Macro Precision:    {multi_prec_macro * 100:.2f}%")
    print(f"Macro Recall:       {multi_rec_macro * 100:.2f}%")
    print(f"Macro-F1 Score:     {multi_f1_macro * 100:.2f}%")
    print(f"Inference Latency:  {multi_infer_time:.4f} ms/record")

    multi_classes = sorted(list(set(y_test_multi)))
    cm_multi = confusion_matrix(y_test_multi, y_pred_multi, labels=multi_classes)
    plot_confusion_matrix(cm_multi, multi_classes, "11-Class IoT Attack Confusion Matrix", figures_dir / "confusion_matrix_multiclass.png")

    # Per-Class Metrics Table
    report_dict = classification_report(y_test_multi, y_pred_multi, labels=multi_classes, output_dict=True, zero_division=0)
    per_class_rows = []
    for cls in multi_classes:
        stats = report_dict[cls]
        per_class_rows.append({
            "class": cls,
            "precision": stats["precision"],
            "recall": stats["recall"],
            "f1_score": stats["f1-score"],
            "support": int(stats["support"])
        })
    df_per_class = pd.DataFrame(per_class_rows)
    df_per_class.to_csv(outputs_dir / "per_class_metrics.csv", index=False)
    print(f"[Table] Per-class metrics saved to {outputs_dir / 'per_class_metrics.csv'}")

    # Model Comparison Summary
    summary_rows = [
        {
            "task": "Task A: Binary",
            "model": bin_model.__class__.__name__,
            "accuracy": bin_acc,
            "precision": bin_prec,
            "recall": bin_rec,
            "f1_score": bin_f1,
            "inference_latency_ms": bin_infer_time,
            "num_test_samples": len(X_test)
        },
        {
            "task": "Task B: Multi-Class",
            "model": multi_model.__class__.__name__,
            "accuracy": multi_acc,
            "precision": multi_prec_macro,
            "recall": multi_rec_macro,
            "f1_score": multi_f1_macro,
            "inference_latency_ms": multi_infer_time,
            "num_test_samples": len(X_test)
        }
    ]
    df_comp = pd.DataFrame(summary_rows)
    df_comp.to_csv(outputs_dir / "model_comparison.csv", index=False)
    print(f"[Table] Model comparison saved to {outputs_dir / 'model_comparison.csv'}")

    return df_comp, df_per_class

if __name__ == "__main__":
    run_evaluation()

