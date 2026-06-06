"""
权限校验装饰器 — Proxy Pattern

作为请求的代理层，拦截未授权请求，
在执行实际视图函数前完成身份验证。
"""

from functools import wraps
from flask import request, g
from jose import JWTError, jwt
from ..extensions import db
from ..models.user import User
from ..utils.response import ApiResponse


def login_required(f):
    """
    登录校验装饰器 — Proxy Pattern

    代理视图函数的执行，在调用前验证 JWT Token。
    验证通过后将当前用户存入 flask.g.current_user。
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()

        if not token:
            return ApiResponse.unauthorized("缺少认证令牌")

        try:
            from flask import current_app
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=[current_app.config.get("JWT_ALGORITHM", "HS256")],
            )
            username = payload.get("sub")
            if username is None:
                return ApiResponse.unauthorized("无效的认证令牌")
        except JWTError:
            return ApiResponse.unauthorized("认证令牌已过期或无效")

        user = db.session.query(User).filter(User.username == username).first()
        if user is None:
            return ApiResponse.unauthorized("用户不存在")

        g.current_user = user
        return f(*args, **kwargs)

    return decorated
