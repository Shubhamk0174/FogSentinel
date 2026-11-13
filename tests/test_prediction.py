import pytest
import pandas as pd
from pathlib import Path
from ml.predict import FogSentinelPredictor

def test_model_artifacts_exist():
    assert Path("artifacts/model/best_binary_model.joblib").exists()
    assert Path("artifacts/model/best_multiclass_model.joblib").exists()

def test_predictor_demo_output():
    predictor = FogSentinelPredictor()
    df_feat = pd.read_csv("data/demo/demo_features.csv")
    preds = predictor.predict_records(df_feat)

    assert len(preds) == 55, "Must produce exactly 55 predictions"
    expected_cols = {"record_id", "prediction", "predicted_attack_type", "confidence", "multi_confidence", "action"}
    assert expected_cols.issubset(set(preds.columns)), f"Missing expected output columns in {preds.columns}"

    # Verify decision actions policy
    for _, row in preds.iterrows():
        if row["prediction"] == "benign":
            assert row["action"] == "ALLOW", f"Benign record must be ALLOW, got {row['action']}"
        else:
            assert row["action"] == "QUARANTINE_RECOMMENDED", f"Malicious record must recommend quarantine, got {row['action']}"
        assert 0.0 <= row["confidence"] <= 1.0, f"Confidence must be probability [0, 1], got {row['confidence']}"

