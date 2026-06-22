import os
from pathlib import Path
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://elearn:elearn@localhost:5432/elearn")

@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def run_sql_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with get_conn() as conn:
        conn.execute(sql)

def run_migrations(directory: str = "migrations") -> list[str]:
    applied = []
    for path in sorted(Path(directory).glob("*.sql")):
        run_sql_file(str(path))
        applied.append(path.name)
    return applied
