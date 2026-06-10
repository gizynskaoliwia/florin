import json
import os
import sys

sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

def main():
    try:
        from views.emergency_fund import EmergencyFundView
        print("Import successful!")
    except Exception as e:
        print(f"Import failed: {e}")

if __name__ == '__main__':
    main()
