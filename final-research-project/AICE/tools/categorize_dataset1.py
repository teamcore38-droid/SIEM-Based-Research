import json
import codecs
from collections import defaultdict
import os

def categorize_dataset():
    input_path = r'c:\Users\acer\Documents\final research\datasets\Dataset1.json'
    output_path = r'c:\Users\acer\Desktop\AICE\data\dataset1_categorized.json'
    
    print("Loading Dataset1.json...")
    try:
        with codecs.open(input_path, 'r', 'utf-16le') as f:
            text = f.read().lstrip('\ufeff')
            data = json.loads(text)
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return

    # Categorization structures
    priority_categories = defaultdict(list)
    attack_categories = defaultdict(list)
    ward_categories = defaultdict(list)
    
    # Statistical counters
    total_records = len(data)
    
    for row in data:
        # Extract features for categorization
        priority = row.get('predicted_priority', 'UNKNOWN')
        attack = row.get('attack_type', 'None')
        ward = row.get('ward', 'UNKNOWN')
        device = row.get('device_id', 'UNKNOWN')
        timestamp = row.get('timestamp')
        
        # We store minimal relevant info to keep the output size manageable
        summary_record = {
            'alert_id': row.get('alert_id'),
            'device_id': device,
            'timestamp': timestamp,
            'confidence': row.get('confidence_score', 0),
            'attack_severity': row.get('attack_severity', 0)
        }
        
        priority_categories[priority].append(summary_record)
        attack_categories[attack].append(summary_record)
        ward_categories[ward].append(summary_record)

    # Build final categorized layout
    categorized_output = {
        "metadata": {
            "source_file": "Dataset1.json",
            "total_records_processed": total_records
        },
        "by_priority": {},
        "by_attack_type": {},
        "by_ward": {}
    }
    
    for p, items in priority_categories.items():
        categorized_output["by_priority"][p] = {
            "count": len(items),
            "alerts": items
        }
    
    for a, items in attack_categories.items():
        categorized_output["by_attack_type"][a] = {
            "count": len(items),
            "unique_devices": list(set(x['device_id'] for x in items))
        }
        
    for w, items in ward_categories.items():
        categorized_output["by_ward"][w] = {
            "count": len(items),
            "unique_devices": list(set(x['device_id'] for x in items))
        }

    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(categorized_output, f, indent=4)
        
    print(f"Dataset categorized successfully. Total Records: {total_records}")
    print(f"Saved categorized output to: {output_path}")
    print("\n--- Summary ---")
    print("Priorities Found:")
    for p, v in categorized_output["by_priority"].items():
        print(f"  - {p}: {v['count']} alerts")
    
    print("\nTop 5 Attack Types Found:")
    sorted_attacks = sorted(categorized_output["by_attack_type"].items(), key=lambda x: x[1]['count'], reverse=True)
    for a, v in sorted_attacks[:5]:
        print(f"  - {a}: {v['count']} alerts (across {len(v['unique_devices'])} devices)")

if __name__ == "__main__":
    categorize_dataset()
