import sys
sys.path.append('c:/Users/ogizy/.gemini/antigravity-ide/scratch/budget_tracker')
import data_manager as dm

def run_migration():
    dm.init_env()
    sp = dm.get_savings_planner()
    recalculated = []
    for cat in sp.get("categories", []):
        nyt = cat.get("next_year_target")
        deadline = cat.get("deadline_month", 12)
        if nyt and deadline < 12:
            monthly_nyt = round(nyt / 12, 2)
            grid_row = sp.get("grid", {}).get(cat["id"], {})
            for m in range(deadline + 1, 13):
                grid_row[f"{m:02d}"] = monthly_nyt
            recalculated.append(cat["name"])
            
    dm.save_savings_planner(sp)
    print(f"Recalculated: {recalculated}")

if __name__ == '__main__':
    run_migration()
