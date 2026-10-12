import sys
from pathlib import Path
from banking.config.settings import get_db_config

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "banking"))

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "database" / "migrations"


def run_migrations() -> None:
    config = get_db_config()
    connection = psycopg.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
    )
    try:
        with connection.cursor() as cur:
            for file_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                print(f"Running: {file_path.name}")
                cur.execute(file_path.read_text(encoding="utf-8"))
        connection.commit()
        print("All migrations applied successfully.")
    except Exception as e:
        connection.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    run_migrations()