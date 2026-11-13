import os
import json
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure matplotlib uses local cache to avoid permission errors
os.environ["MPLCONFIGDIR"] = str(Path(".cache/matplotlib").resolve())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_config(config_path="config/data.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def extract_and_save_schema(schema_source="data/raw/demonstrate_structure.csv", schema_target="artifacts/feature_schema.json"):
    Path(schema_target).parent.mkdir(parents=True, exist_ok=True)
    with open(schema_source, "r") as f:
        header = f.readline().strip()
    columns = [c.strip() for c in header.split(",") if c.strip()]
    if len(columns) != 115:
        raise ValueError(f"Expected 115 columns in schema, found {len(columns)}")
    
    schema_data = {
        "feature_count": len(columns),
        "features": columns
    }
    with open(schema_target, "w") as f:
        json.dump(schema_data, f, indent=2)
    print(f"[Schema] Validated {len(columns)} feature columns and saved schema to {schema_target}")
    return columns

def prepare_dataset(config_path="config/data.yaml"):
    config = load_config(config_path)
    feature_columns = extract_and_save_schema()
    
    raw_dir = Path(config["raw_data_dir"]) / config["target_device"]
    processed_dir = Path(config["processed_data_dir"])
    demo_dir = Path(config["demo_data_dir"])
    outputs_fig_dir = Path("outputs/figures")
    outputs_model_dir = Path("outputs/model")
    
    for d in [processed_dir, demo_dir, outputs_fig_dir, outputs_model_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    sampling_cfg = config["sampling"]
    samples_per_class = sampling_cfg["samples_per_class"]
    seed = sampling_cfg["random_seed"]
    np.random.seed(seed)
    
    classes_info = config["classes"]
    
    demo_features_list = []
    demo_labels_list = []
    
    train_records = []
    val_records = []
    test_records = []
    
    summary_rows = []
    
    print("\n[Data Ingestion] Ingesting and validating class files from UCI N-BaIoT...")
    
    for class_key, meta in classes_info.items():
        file_path = raw_dir / meta["file"]
        if not file_path.exists():
            raise FileNotFoundError(f"Missing raw data file: {file_path}")
            
        # Count total rows
        with open(file_path, "rb") as f:
            total_source_rows = sum(1 for _ in f) - 1
            
        # Determine demo sample count
        is_benign = (class_key == "benign")
        demo_count = sampling_cfg["demo_benign_count"] if is_benign else sampling_cfg["demo_attack_per_class"]
        
        # Read a chunk that comfortably covers demo + samples_per_class
        # Read header and up to 2 * samples_per_class rows
        chunk_to_read = min(total_source_rows, samples_per_class + demo_count + 2000)
        df_chunk = pd.read_csv(file_path, nrows=chunk_to_read)
        
        # Verify 115 columns
        if len(df_chunk.columns) != 115:
            raise ValueError(f"File {file_path} has {len(df_chunk.columns)} columns, expected 115")
            
        # Ensure column alignment
        df_chunk.columns = feature_columns
        
        # Clean infinities and NaNs
        df_chunk = df_chunk.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Shuffle deterministically
        df_chunk = df_chunk.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        
        # Take demo rows FIRST so there is zero overlap with train/val/test
        df_demo_class = df_chunk.iloc[:demo_count].copy()
        df_model_pool = df_chunk.iloc[demo_count:demo_count + samples_per_class].copy()
        
        # Store demo features and separate demo labels
        for idx, row in df_demo_class.iterrows():
            demo_features_list.append(row[feature_columns].to_dict())
            demo_labels_list.append({
                "binary_label": meta["binary_label"],
                "multi_label": meta["multi_label"]
            })
            
        # Add labels to model pool
        df_model_pool["binary_label"] = meta["binary_label"]
        df_model_pool["multi_label"] = meta["multi_label"]
        df_model_pool["device"] = config["target_device"]
        
        # Split model pool into Train (70%), Val (15%), Test (15%)
        n = len(df_model_pool)
        n_train = int(n * config["split"]["train_ratio"])
        n_val = int(n * config["split"]["val_ratio"])
        
        train_records.append(df_model_pool.iloc[:n_train])
        val_records.append(df_model_pool.iloc[n_train:n_train + n_val])
        test_records.append(df_model_pool.iloc[n_train + n_val:])
        
        summary_rows.append({
            "class": class_key,
            "binary_label": meta["binary_label"],
            "source_file": meta["file"],
            "total_source_rows": total_source_rows,
            "sampled_rows": n,
            "train_rows": n_train,
            "val_rows": n_val,
            "test_rows": n - n_train - n_val,
            "demo_rows": demo_count
        })
        print(f"  Processed {class_key:15s} | Source: {total_source_rows:7d} rows | Sampled: {n:5d} (Train: {n_train:5d}, Val: {n_val:4d}, Test: {n - n_train - n_val:4d}) | Demo: {demo_count}")
        
    # Save Demo CSVs
    df_demo_feat = pd.DataFrame(demo_features_list)
    df_demo_feat = df_demo_feat[feature_columns] # Strict column order
    df_demo_feat.to_csv(demo_dir / "demo_features.csv", index=False)
    
    df_demo_lab = pd.DataFrame(demo_labels_list)
    df_demo_lab.insert(0, "record_id", [f"REC_{i:03d}" for i in range(len(df_demo_lab))])
    df_demo_lab.to_csv(demo_dir / "demo_labels.csv", index=False)
    
    print(f"\n[Demo Set] Saved demo_features.csv: {df_demo_feat.shape} (55 records x 115 features)")
    print(f"[Demo Set] Saved demo_labels.csv: {df_demo_lab.shape} (Labels stored strictly separately)")
    print(f"           Benign demo count: {(df_demo_lab['binary_label'] == 'benign').sum()}")
    print(f"           Malicious demo count: {(df_demo_lab['binary_label'] == 'malicious').sum()}")
    
    # Concatenate and save Train / Val / Test
    df_train = pd.concat(train_records, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df_val = pd.concat(val_records, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df_test = pd.concat(test_records, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    
    df_train.to_csv(processed_dir / "train.csv", index=False)
    df_val.to_csv(processed_dir / "val.csv", index=False)
    df_test.to_csv(processed_dir / "test.csv", index=False)
    
    print(f"\n[Dataset Split] Train shape: {df_train.shape} | Val shape: {df_val.shape} | Test shape: {df_test.shape}")
    
    # Save Summary CSV
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(outputs_model_dir / "dataset_summary.csv", index=False)
    print(f"[Summary] Saved dataset summary to {outputs_model_dir / 'dataset_summary.csv'}")
    
    # Plot Class Distribution Chart
    plt.figure(figsize=(10, 5))
    bars = plt.bar(df_summary["class"], df_summary["sampled_rows"], color="steelblue", edgecolor="black")
    plt.title("N-BaIoT Sampled Training/Evaluation Instances per Class")
    plt.xlabel("Traffic Class")
    plt.ylabel("Number of Instances")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    chart_path = outputs_fig_dir / "dataset_distribution.png"
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"[Figure] Saved class distribution chart to {chart_path}")
    
    return df_train, df_val, df_test, df_demo_feat, df_demo_lab

if __name__ == "__main__":
    prepare_dataset()

