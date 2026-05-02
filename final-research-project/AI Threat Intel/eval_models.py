import pandas as pd
import pickle
from sklearn.metrics import confusion_matrix
import sys
import os

print("--- AI THREAT INTEL RF ---")
try:
    with open('random_forest_model.pkl', 'rb') as f:
        m = pickle.load(f)
    print("Loaded RF.")
except Exception as e:
    print("Error:", e)

# The training script used "X:/AI-TI/data/combined_dataset.csv" we'll search locally
data_path = 'detection_results.csv'
print(f"Loading {data_path}...")
df = pd.read_csv(data_path)
print("DF columns:", df.columns)
