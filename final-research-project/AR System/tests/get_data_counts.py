import pandas as pd
import json
import os

base = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System\data"

print("DATA_COUNTS_START")
with open(os.path.join(base, "optimized_threat_triggers.json"), "r") as f:
    df1 = pd.DataFrame(json.load(f))
    print("RESPONSE:", df1['action_required'].value_counts().to_json())

with open(os.path.join(base, "optimized_phi_logs.json"), "r") as f:
    df2 = pd.DataFrame(json.load(f))
    print("PHI:", df2['phi_present'].value_counts().to_json())
print("DATA_COUNTS_END")
