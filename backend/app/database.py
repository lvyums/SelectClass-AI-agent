import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .core.config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_mysql_url = (
    f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    f"?charset=utf8mb4"
)

try:
    _test_engine = create_engine(_mysql_url, future=True, pool_pre_ping=True)
    with _test_engine.connect():
        pass
    DATABASE_URL = _mysql_url
    logger.info("Using MySQL: %s:%s/%s", settings.db_host, settings.db_port, settings.db_name)
except Exception:
    _sqlite_path = PROJECT_ROOT / "course_selection.db"
    DATABASE_URL = f"sqlite:///{_sqlite_path}"
    logger.warning("MySQL unavailable, falling back to SQLite: %s", _sqlite_path)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
