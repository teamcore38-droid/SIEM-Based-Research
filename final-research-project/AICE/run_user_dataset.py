import sys
import os

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import AICE

def main():
    print("=== AICE User Dataset Runner ===")
    
    # Path to the user's CSV file
    input_file = r"c:\Users\acer\Documents\final research\datasets\predictions_with_results.csv"
    output_file = "data/user_incidents.json"
    
    print(f"Input File: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file {input_file} not found.")
        return

    aice = AICE()
    try:
        aice.run(input_file, output_file)
        print(f"\n[SUCCESS] Results saved to {output_file}")
        
        # Determine CSV output path
        output_csv = output_file.replace('.json', '.csv')
        
        # Convert JSON output to CSV for easier viewing (optional but helpful)
        try:
            import json
            import csv
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            if data:
                with open(output_csv, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                print(f"[SUCCESS] Convert results to CSV: {output_csv}")
        except Exception as e:
            print(f"Warning: Failed to convert output to CSV: {e}")

    except Exception as e:
        print(f"[CRITICAL FAILURE] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
