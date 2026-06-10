import json
import os
import sys

sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

def main():
    settings = dm.get_emergency_fund_settings()
    for mode, data in settings.items():
        print(f"--- MODE: {mode} ---")
        actual_saved = data.get("actual_saved", 0.0)
        print(f"Actual Saved: {actual_saved}")
        
        salary = data.get("salary", 0.0)
        mortgage = data.get("mortgage", 0.0)
        living = data.get("living_expenses", 0.0)
        print(f"salary: {salary}, mortgage: {mortgage}, living: {living}")
        
        goal_labels = {
            "3msc_zycia": "3msc życia",
            "6msc_zycia": "6msc życia",
            "3msc_kredytu": "3msc kredytu",
            "6msc_kredytu": "6msc kredytu",
            "3msc_zycia_kredytu": "3msc życia + kredytu",
            "4msc_zycia_kredytu": "4msc życia + kredytu",
            "5msc_zycia_kredytu": "5msc życia + kredytu",
            "6msc_zycia_kredytu": "6msc życia + kredytu",
            "3msc_wyplaty": "3msc wypłaty",
            "6msc_wyplaty": "6msc wypłaty",
        }
        
        for key in goal_labels.keys():
            target = 0.0
            if key == "3msc_zycia": target = 3 * living
            elif key == "6msc_zycia": target = 6 * living
            elif key == "3msc_kredytu": target = 3 * mortgage
            elif key == "6msc_kredytu": target = 6 * mortgage
            elif key == "3msc_zycia_kredytu": target = 3 * (living + mortgage)
            elif key == "4msc_zycia_kredytu": target = 4 * (living + mortgage)
            elif key == "5msc_zycia_kredytu": target = 5 * (living + mortgage)
            elif key == "6msc_zycia_kredytu": target = 6 * (living + mortgage)
            elif key == "3msc_wyplaty": target = 3 * salary
            elif key == "6msc_wyplaty": target = 6 * salary
            
            is_completed = target <= actual_saved
            print(f"Goal: {key:20} Target: {target:10.2f} Completed: {is_completed}")
            
if __name__ == '__main__':
    main()
