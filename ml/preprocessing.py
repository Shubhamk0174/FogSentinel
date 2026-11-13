import os
import json
import joblib
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

SCHEMA_PATH = "artifacts/feature_schema.json"
SCALER_PATH = "artifacts/scaler/standard_scaler.joblib"

def load_schema(schema_path=SCHEMA_PATH):
    with open(schema_path, "r") as f:
        data = json.load(f)
    return data["features"]

class PreprocessingPipeline:
    def __init__(self, schema_path=SCHEMA_PATH):
        self.schema_columns = load_schema(schema_path)
        self.scaler = StandardScaler()
        self.is_fitted = False

    def validate_and_align_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates feature presence and strictly aligns column ordering to the schema.
        Rejects inputs with missing features. Safely ignores label columns if present.
        """
        # If input has no column names or standard integer indices
        if isinstance(df.columns, pd.RangeIndex):
            if df.shape[1] != len(self.schema_columns):
                raise ValueError(f"Input matrix has {df.shape[1]} columns, expected {len(self.schema_columns)}")
            df = df.copy()
            df.columns = self.schema_columns
            return df

        missing_cols = set(self.schema_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Input is missing {len(missing_cols)} required schema features. Examples: {list(missing_cols)[:5]}")

        # Reorder to match exact canonical schema
        df_aligned = df[self.schema_columns].copy()
        return df_aligned

    def clean_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Replaces infinite values with column medians or zeros and fills NaNs.
        """
        df_clean = df.copy()
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
        if df_clean.isna().any().any():
            df_clean = df_clean.fillna(0.0)
        return df_clean

    def fit(self, df_train: pd.DataFrame):
        """
        Fits StandardScaler on training data only.
        """
        features_df = self.validate_and_align_features(df_train)
        features_clean = self.clean_values(features_df)
        self.scaler.fit(features_clean.values)
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Applies fitted StandardScaler to input features.
        """
        if not self.is_fitted:
            raise RuntimeError("Pipeline is not fitted yet. Call fit() or load_scaler() first.")
        features_df = self.validate_and_align_features(df)
        features_clean = self.clean_values(features_df)
        return self.scaler.transform(features_clean.values)

    def fit_transform(self, df_train: pd.DataFrame) -> np.ndarray:
        return self.fit(df_train).transform(df_train)

    def save(self, scaler_path=SCALER_PATH):
        Path(scaler_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, scaler_path)
        print(f"[Preprocessing] Saved fitted scaler to {scaler_path}")

    def load(self, scaler_path=SCALER_PATH):
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Fitted scaler not found at {scaler_path}")
        self.scaler = joblib.load(scaler_path)
        self.is_fitted = True
        return self

def run_preprocessing_pipeline():
    print("[Preprocessing] Loading split datasets from data/processed...")
    train_df = pd.read_csv("data/processed/train.csv")
    val_df = pd.read_csv("data/processed/val.csv")
    test_df = pd.read_csv("data/processed/test.csv")

    pipeline = PreprocessingPipeline()
    print("[Preprocessing] Fitting StandardScaler strictly on Train set...")
    X_train = pipeline.fit_transform(train_df)
    pipeline.save()

    print("[Preprocessing] Transforming Val and Test sets using fitted scaler...")
    X_val = pipeline.transform(val_df)
    X_test = pipeline.transform(test_df)

    # Save processed arrays
    np.save("data/processed/X_train.npy", X_train)
    np.save("data/processed/X_val.npy", X_val)
    np.save("data/processed/X_test.npy", X_test)

    # Save target vectors
    train_df[["binary_label", "multi_label"]].to_csv("data/processed/y_train.csv", index=False)
    val_df[["binary_label", "multi_label"]].to_csv("data/processed/y_val.csv", index=False)
    test_df[["binary_label", "multi_label"]].to_csv("data/processed/y_test.csv", index=False)

    print(f"[Preprocessing] Complete! X_train: {X_train.shape}, X_val: {X_val.shape}, X_test: {X_test.shape}")
    return pipeline

if __name__ == "__main__":
    run_preprocessing_pipeline()

