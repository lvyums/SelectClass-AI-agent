"""
配置单例模块 — Singleton Pattern

使用 python-dotenv 加载 .env 文件，提供全局唯一的配置实例。
支持多环境切换（development / testing / production）。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """基础配置（单例基类）"""

    # Flask
    SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key")
    DEBUG = False
    TESTING = False

    # 数据库
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "course_selection")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 8

    # MiMo LLM
    MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
    MIMO_API_URL = os.getenv("MIMO_API_URL", "https://api.mimo.example/v1/chat/completions")
    MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-1")

    # CORS
    CORS_ORIGINS = ["http://localhost:5173"]

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """优先尝试 MySQL，失败则回退 SQLite"""
        mysql_url = (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )
        try:
            import pymysql
            conn = pymysql.connect(
                host=self.DB_HOST, port=self.DB_PORT,
                user=self.DB_USER, password=self.DB_PASSWORD,
                database=self.DB_NAME,
            )
            conn.close()
            return mysql_url
        except Exception:
            sqlite_path = PROJECT_ROOT / "course_selection.db"
            return f"sqlite:///{sqlite_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DB_NAME = "course_selection_test"


class ProductionConfig(Config):
    pass


# 配置映射 — 全局唯一入口
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
