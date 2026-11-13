import json
import pytest
import pandas as pd
from pathlib import Path

def test_schema_json():
    schema_path = Path("artifacts/feature_schema.json")
    assert schema_path.exists(), "Feature schema JSON must exist"
    with open(schema_path, "r") as f:
        schema = json.load(f)
    assert schema["feature_count"] == 115, "Feature count must be exactly 115"
    assert len(schema["features"]) == 115, "Feature list must have 115 names"

def test_demo_csv_dimensions():
    feat_path = Path("data/demo/demo_features.csv")
    lab_path = Path("data/demo/demo_labels.csv")
    assert feat_path.exists(), "demo_features.csv must exist"
    assert lab_path.exists(), "demo_labels.csv must exist"

    df_feat = pd.read_csv(feat_path)
    df_lab = pd.read_csv(lab_path)

    assert df_feat.shape == (55, 115), f"demo_features must be (55, 115), got {df_feat.shape}"
    assert len(df_lab) == 55, f"demo_labels must have 55 rows, got {len(df_lab)}"
    
    # Ensure no label leakage in demo_features
    for col in ["binary_label", "multi_label", "label", "class"]:
        assert col not in df_feat.columns, f"Label column '{col}' leaked into demo_features.csv"

def test_feature_data_types():
    df_feat = pd.read_csv("data/demo/demo_features.csv")
    for col in df_feat.columns:
        assert pd.api.types.is_numeric_dtype(df_feat[col]), f"Feature column '{col}' is not numeric"

