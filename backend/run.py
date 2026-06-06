"""
Flask 应用入口 — 启动开发服务器

使用方式：
    python run.py
    或
    flask --app run:app run --port 4000
"""

import os
import logging
from app import create_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

config_name = os.getenv("FLASK_ENV", "default")
app = create_app(config_name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
