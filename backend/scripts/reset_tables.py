import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from sqlalchemy import create_engine, text


def main():
    engine = create_engine(
        f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
        future=True,
    )
    conn = engine.execution_options(isolation_level="AUTOCOMMIT").connect()
    for tbl in ("selections", "user_history", "courses", "users"):
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
            print(f"dropped {tbl} (if existed)")
        except Exception as e:
            print(f"error dropping {tbl}: {e}")
    conn.close()

if __name__ == "__main__":
    main()
