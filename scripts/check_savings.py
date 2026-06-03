import sys
sys.path.append('c:/Users/ogizy/.gemini/antigravity-ide/scratch/budget_tracker')
import data_manager as dm

dm.init_env()
sp = dm.get_savings_planner()
cats = sp.get("categories", [])
print(f"Categories count: {len(cats)}")
for c in cats:
    print(f" - {c.get('name')}: group={c.get('group')}, hidden={c.get('hidden')}, id={c.get('id')}")
