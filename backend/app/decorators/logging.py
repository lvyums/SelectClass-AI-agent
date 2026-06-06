"""
请求日志装饰器 — Decorator Pattern

为视图函数附加日志记录行为，不修改原函数逻辑。
"""

import time
import logging
from functools import wraps
from flask import request

logger = logging.getLogger(__name__)


def log_request(f):
    """
    请求日志装饰器 — Decorator Pattern

    装饰视图函数，附加请求日志记录功能：
    - 记录请求方法和路径
    - 记录响应耗时
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        start = time.time()
        logger.info("→ %s %s", request.method, request.path)
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        logger.info("← %s %s (%.3fs)", request.method, request.path, elapsed)
        return result

    return decorated
