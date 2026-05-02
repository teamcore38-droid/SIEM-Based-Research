import json
import os
import pandas as pd

path = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System\data\optimized_threat_triggers.json"
print("Reading...")
try:
    with open(path, 'r') as f:
        d = json.load(f)
    print("Loaded. Type:", type(d))
    if isinstance(d, list):
        print("List len:", len(d))
        print("Item 0 type:", type(d[0]))
    
    df = pd.DataFrame(d)
    print("DF shape:", df.shape)
except Exception as e:
    import traceback
    traceback.print_exc()
