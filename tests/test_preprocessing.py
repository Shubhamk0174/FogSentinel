import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from ml.preprocessing import PreprocessingPipeline, SCALER_PATH

def test_scaler_artifact_exists():
    assert Path(SCALER_PATH).exists(), f"Fitted scaler must exist at {SCALER_PATH}"

def test_pipeline_transform_shape():
    df_demo = pd.read_csv("data/demo/demo_features.csv")
    pipeline = PreprocessingPipeline().load()
    X = pipeline.transform(df_demo)
    assert X.shape == (55, 115), f"Transformed shape must be (55, 115), got {X.shape}"
    assert isinstance(X, np.ndarray), "Output must be a numpy ndarray"

def test_pipeline_rejects_missing_columns():
    df_demo = pd.read_csv("data/demo/demo_features.csv")
    df_invalid = df_demo.drop(columns=[df_demo.columns[0]])
    pipeline = PreprocessingPipeline().load()
    with pytest.raises(ValueError, match="missing"):
        pipeline.transform(df_invalid)

def test_pipeline_column_reordering_alignment():
    df_demo = pd.read_csv("data/demo/demo_features.csv")
    # Reverse column order
    reversed_cols = list(reversed(df_demo.columns))
    df_reversed = df_demo[reversed_cols]
    
    pipeline = PreprocessingPipeline().load()
    X_orig = pipeline.transform(df_demo)
    X_reordered = pipeline.transform(df_reversed)
    
    np.testing.assert_allclose(X_orig, X_reordered, rtol=1e-5, atol=1e-5,
                               err_msg="Pipeline must safely align reordered columns to canonical schema")

