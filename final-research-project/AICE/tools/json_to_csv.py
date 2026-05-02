import json
import csv
import os

def convert_to_csv(json_file, csv_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        if not data:
            print("No data to convert.")
            return

        # Get headers from the first dictionary
        headers = list(data[0].keys())

        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for entry in data:
                row = []
                for h in headers:
                    val = entry.get(h, "")
                    # specialized handling for lists (compliance_tags)
                    if isinstance(val, list):
                        val = "; ".join(val)
                    row.append(val)
                writer.writerow(row)
        
        print(f"Successfully converted {json_file} to {csv_file}")

    except Exception as e:
        print(f"Error converting to CSV: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        convert_to_csv(sys.argv[1], sys.argv[2])
    else:
        convert_to_csv("data/detection_incidents.json", "data/detection_incidents.csv")
