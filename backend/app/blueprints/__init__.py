"""蓝图模块 — Blueprint Pattern

每个业务模块的路由独立封装为蓝图，在 create_app() 中统一注册。
"""

from .auth import auth_bp
from .courses import courses_bp
from .selection import selection_bp
from .profile import profile_bp
from .recommendations import recommendations_bp
from .chat import chat_bp

__all__ = ["auth_bp", "courses_bp", "selection_bp", "profile_bp", "recommendations_bp", "chat_bp"]
