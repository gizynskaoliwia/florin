import main
from main import FlorinApp, tx, display_category_name

def test_add_expense():
    app = FlorinApp()
    data = app.data
    split_cats = data.get('categories', [])
    active_source_id = 'daily_life'
    
    source_options = {}
    for c in split_cats:
        source_options[f"{tx('Budget')}: {display_category_name(c)}"] = ('budget', c['id'])
    
    cur_split = next((f"{tx('Budget')}: {display_category_name(c)}" for c in split_cats if c['id'] == active_source_id), None)
    
    print('Options keys:', list(source_options.keys()))
    print('Cur split:', cur_split)
    print('Matches?', cur_split in source_options)

if __name__ == '__main__':
    test_add_expense()
