"""
认证蓝图 — Blueprint Pattern

处理用户注册、登录、获取当前用户信息。
使用 @login_required 装饰器（Proxy Pattern）保护需要认证的接口。
使用 @log_request 装饰器（Decorator Pattern）记录请求日志。
"""

import time
from collections import defaultdict
from threading import Lock
from flask import Blueprint, request, g
from ..decorators import login_required, log_request
from ..services import auth_service
from ..utils.response import ApiResponse
from ..utils.validators import validate_required, validate_length

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# 限流器
class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        self._cleanup_counter = 0

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            self._cleanup_counter += 1
            if self._cleanup_counter >= 100:
                self._cleanup_stale(now)
                self._cleanup_counter = 0
            timestamps = self._requests[key]
            self._requests[key] = [t for t in timestamps if now - t < self.window_seconds]
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True

    def _cleanup_stale(self, now: float) -> None:
        """清理窗口期外的过期条目，防止内存泄漏"""
        stale_keys = [
            k for k, v in self._requests.items()
            if all(now - t >= self.window_seconds for t in v)
        ]
        for k in stale_keys:
            del self._requests[k]

_login_limiter = RateLimiter(max_requests=10, window_seconds=60)
_register_limiter = RateLimiter(max_requests=5, window_seconds=60)


def _get_client_ip() -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


@auth_bp.route("/register", methods=["POST"])
@log_request
def register():
    """用户注册"""
    client_ip = _get_client_ip()
    if not _register_limiter.is_allowed(client_ip):
        return ApiResponse.too_many("注册请求过于频繁，请稍后再试。")

    data = request.get_json(silent=True) or {}
    error = validate_required(data, ["username", "password"])
    if error:
        return ApiResponse.error(error)

    error = validate_length(data["username"], "用户名", min_len=2, max_len=100)
    if error:
        return ApiResponse.error(error)
    error = validate_length(data["password"], "密码", min_len=6, max_len=128)
    if error:
        return ApiResponse.error(error)

    result = auth_service.register_user(
        username=data["username"],
        password=data["password"],
        major=data.get("major", ""),
        grade=data.get("grade", ""),
        interests=data.get("interests", ""),
    )
    if not result["success"]:
        return ApiResponse.error(result["error"])

    user = result["user"]
    return ApiResponse.success({
        "access_token": result["token"],
        "token_type": "bearer",
        "user": user.to_dict(),
    })


@auth_bp.route("/login", methods=["POST"])
@log_request
def login():
    """用户登录"""
    client_ip = _get_client_ip()
    if not _login_limiter.is_allowed(client_ip):
        return ApiResponse.too_many("登录请求过于频繁，请稍后再试。")

    data = request.get_json(silent=True) or {}
    error = validate_required(data, ["username", "password"])
    if error:
        return ApiResponse.error(error)

    result = auth_service.authenticate_user(data["username"], data["password"])
    if not result["success"]:
        return ApiResponse.error(result["error"], 401)

    user = result["user"]
    return ApiResponse.success({
        "access_token": result["token"],
        "token_type": "bearer",
        "user": user.to_dict(),
    })


@auth_bp.route("/me", methods=["GET"])
@login_required
@log_request
def me():
    """获取当前用户信息"""
    return ApiResponse.success({"user": g.current_user.to_dict()})
