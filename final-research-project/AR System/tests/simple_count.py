import pandas as pd, json, os
base = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System\data"
df = pd.DataFrame(json.load(open(os.path.join(base, "optimized_threat_triggers.json"))))
print(f"Total: {len(df)}")
print(df['action_required'].value_counts())
