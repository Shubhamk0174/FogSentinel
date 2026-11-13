import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import joblib
import numpy as np
import pandas as pd
from ml.preprocessing import PreprocessingPipeline

class FogSentinelPredictor:
    def __init__(self,
                 scaler_path="artifacts/scaler/standard_scaler.joblib",
                 binary_model_path="artifacts/model/best_binary_model.joblib",
                 multiclass_model_path="artifacts/model/best_multiclass_model.joblib",
                 schema_path="artifacts/feature_schema.json"):
        
        self.pipeline = PreprocessingPipeline(schema_path=schema_path)
        self.pipeline.load(scaler_path)
        
        if not os.path.exists(binary_model_path):
            raise FileNotFoundError(f"Binary model checkpoint not found at {binary_model_path}")
        self.binary_model = joblib.load(binary_model_path)
        
        if not os.path.exists(multiclass_model_path):
            raise FileNotFoundError(f"Multiclass model checkpoint not found at {multiclass_model_path}")
        self.multiclass_model = joblib.load(multiclass_model_path)
        
    def predict_records(self, df_input: pd.DataFrame) -> pd.DataFrame:
        """
        Accepts raw or unnormalized DataFrame of 115 network statistical features.
        Validates column names and ordering against canonical schema.
        Transforms using fitted StandardScaler.
        Returns detailed predictions DataFrame.
        """
        # Validate and transform
        X_scaled = self.pipeline.transform(df_input)
        
        # 1. Binary predictions & probabilities
        bin_preds = self.binary_model.predict(X_scaled)
        if hasattr(self.binary_model, "predict_proba"):
            bin_probs = self.binary_model.predict_proba(X_scaled)
            bin_classes = list(self.binary_model.classes_)
            # Confidence is max class probability
            bin_conf = np.max(bin_probs, axis=1)
        else:
            bin_conf = np.ones(len(bin_preds))
            
        # 2. Multi-class predictions & probabilities
        multi_preds = self.multiclass_model.predict(X_scaled)
        if hasattr(self.multiclass_model, "predict_proba"):
            multi_probs = self.multiclass_model.predict_proba(X_scaled)
            multi_conf = np.max(multi_probs, axis=1)
        else:
            multi_conf = np.ones(len(multi_preds))
            
        # 3. Decision Policy
        # benign -> ALLOW
        # malicious -> QUARANTINE_RECOMMENDED
        actions = [
            "ALLOW" if p == "benign" else "QUARANTINE_RECOMMENDED"
            for p in bin_preds
        ]
        
        results = []
        for i in range(len(df_input)):
            rec_id = f"REC_{i:03d}"
            results.append({
                "record_id": rec_id,
                "prediction": bin_preds[i],
                "predicted_attack_type": multi_preds[i],
                "confidence": round(float(bin_conf[i]), 4),
                "multi_confidence": round(float(multi_conf[i]), 4),
                "action": actions[i]
            })
            
        return pd.DataFrame(results)

def run_demo_prediction(input_csv="data/demo/demo_features.csv",
                        output_csv="outputs/demo/demo_predictions.csv",
                        ground_truth_csv="data/demo/demo_labels.csv"):
    
    print("=========================================================================")
    print("             FogSentinel — Interactive Prediction Demonstration          ")
    print("=========================================================================")
    
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Demo feature input CSV not found at {input_csv}")
        
    df_features = pd.read_csv(input_csv)
    print(f"Loaded input features from: {input_csv}")
    print(f"Input Matrix Dimensions:    {df_features.shape[0]} rows x {df_features.shape[1]} features")
    
    predictor = FogSentinelPredictor()
    df_preds = predictor.predict_records(df_features)
    
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df_preds.to_csv(output_csv, index=False)
    print(f"Predictions successfully saved to: {output_csv}\n")
    
    total = len(df_preds)
    benign_cnt = (df_preds["prediction"] == "benign").sum()
    malicious_cnt = (df_preds["prediction"] == "malicious").sum()
    
    print("--- [Prediction Summary] ---")
    print(f"Total Records Processed: {total}")
    print(f"Predicted BENIGN:        {benign_cnt} ({(benign_cnt/total)*100:.1f}%) -> Action: ALLOW")
    print(f"Predicted MALICIOUS:     {malicious_cnt} ({(malicious_cnt/total)*100:.1f}%) -> Action: QUARANTINE_RECOMMENDED")
    
    # Ground truth validation view
    if os.path.exists(ground_truth_csv):
        df_labels = pd.read_csv(ground_truth_csv)
        matches = (df_preds["prediction"] == df_labels["binary_label"]).sum()
        multi_matches = (df_preds["predicted_attack_type"] == df_labels["multi_label"]).sum()
        print("\n--- [Ground-Truth Verification View] ---")
        print(f"Binary Agreement:       {matches} / {total} ({(matches/total)*100:.1f}%)")
        print(f"Multi-Class Agreement:  {multi_matches} / {total} ({(multi_matches/total)*100:.1f}%)")
        
    print("\n--- [First 10 Sample Predictions] ---")
    display_cols = ["record_id", "prediction", "predicted_attack_type", "confidence", "action"]
    print(df_preds[display_cols].head(10).to_string(index=False))
    
    return df_preds

if __name__ == "__main__":
    run_demo_prediction()

