import json
import os
import sys

sys.path.append(r"c:\Users\ogizy\.gemini\antigravity-ide\scratch\budget_tracker")
import data_manager as dm

def calculate_target(mode_data, is_future=False):
    salary = mode_data.get("salary", 0.0)
    mortgage = mode_data.get("mortgage", 0.0)
    living = mode_data.get("living_expenses", 0.0)
    goal = mode_data.get("future_goal", "6msc_zycia") if is_future else mode_data.get("selected_goal", "3msc_zycia")
    
    if goal == "3msc_zycia": return 3 * living
    elif goal == "6msc_zycia": return 6 * living
    elif goal == "3msc_kredytu": return 3 * mortgage
    elif goal == "6msc_kredytu": return 6 * mortgage
    elif goal == "3msc_zycia_kredytu": return 3 * (living + mortgage)
    elif goal == "4msc_zycia_kredytu": return 4 * (living + mortgage)
    elif goal == "5msc_zycia_kredytu": return 5 * (living + mortgage)
    elif goal == "6msc_zycia_kredytu": return 6 * (living + mortgage)
    elif goal == "3msc_wyplaty": return 3 * salary
    elif goal == "6msc_wyplaty": return 6 * salary
    return 0.0

def main():
    settings = dm.get_emergency_fund_settings()
    for mode, data in settings.items():
        print(f"\n--- MODE: {mode} ---")
        actual_saved = data.get("actual_saved", 0.0)
        
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
        
        system_goal_keys = list(goal_labels.keys())
        active_goal_key = data.get("selected_goal", "3msc_zycia")
        future_goal_key = data.get("future_goal", "6msc_zycia")
        
        combined_goals = []
        for key in system_goal_keys:
            temp_data = dict(data)
            temp_data["selected_goal"] = key
            target = calculate_target(temp_data, is_future=False)
            
            is_active = (key == active_goal_key)
            is_future = (key == future_goal_key)
            
            if actual_saved >= target or is_active or is_future:
                combined_goals.append({
                    "name": goal_labels.get(key, key), 
                    "target": target, 
                })
        print(f"Combined goals before custom: {combined_goals}")

if __name__ == '__main__':
    main()
