import os
import shutil
import datetime
from pathlib import Path

def backup_db():
    db_path = Path.home() / 'AppData' / 'Local' / 'Florin' / 'florin.db'
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    backup_dir = Path.home() / 'AppData' / 'Local' / 'Florin' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"florin_backup_{timestamp}.db"

    shutil.copy2(db_path, backup_path)
    print(f"Successfully backed up database to {backup_path}")

if __name__ == "__main__":
    backup_db()
