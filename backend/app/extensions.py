"""
扩展实例模块 — Singleton Pattern

所有 Flask 扩展在此创建全局唯一实例，
在 create_app() 中通过 init_app() 初始化。
"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# 数据库单例 — 全局唯一 SQLAlchemy 实例
db = SQLAlchemy()

# CORS 单例
cors = CORS()
