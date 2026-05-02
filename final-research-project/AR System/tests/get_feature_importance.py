import pickle
import os
import pandas as pd
import numpy as np

BASE_DIR = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System"
MODEL_PATH = os.path.join(BASE_DIR, "models", "ars_response_model.pkl")

def get_importances():
    print("Loading model...")
    if not os.path.exists(MODEL_PATH):
        print("Model file not found.")
        return

    with open(MODEL_PATH, 'rb') as f:
        bundle = pickle.load(f)
    
    if isinstance(bundle, dict):
        model = bundle['model']
    else:
        model = bundle
        
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        # Features used in training: ['threat_type', 'severity', 'confidence_score']
        feature_names = ['Threat Type', 'Severity Level', 'Confidence Score']
        
        # Create a dataframe for nicer printing
        df_imp = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        df_imp = df_imp.sort_values(by='Importance', ascending=False)
        
        print("\n=== AR SYSTEM FEATURE IMPORTANCE ===")
        for index, row in df_imp.iterrows():
            print(f"{row['Feature']}: {row['Importance']*100:.1f}%")
    else:
        print("Model does not support feature importance (not a tree-based model?).")

if __name__ == "__main__":
    get_importances()
