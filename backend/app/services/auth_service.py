"""
认证服务 — 封装密码哈希、JWT 生成、用户验证逻辑
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config import config
from ..extensions import db
from ..models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain, hashed)


def create_token(username: str) -> str:
    """生成 JWT Token"""
    cfg = config["default"]
    expire = datetime.utcnow() + timedelta(hours=cfg.JWT_EXPIRATION_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, cfg.JWT_SECRET, algorithm=cfg.JWT_ALGORITHM)


def decode_token(token: str) -> str | None:
    """解码 JWT Token，返回 username 或 None"""
    cfg = config["default"]
    try:
        payload = jwt.decode(token, cfg.JWT_SECRET, algorithms=[cfg.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def register_user(username: str, password: str, major: str = "", grade: str = "", interests: str = "") -> dict:
    """注册新用户，返回 {success, user, token, error}"""
    existing = db.session.query(User).filter(User.username == username).first()
    if existing:
        return {"success": False, "error": "注册失败，请更换用户名后重试。"}

    user = User(
        username=username,
        password_hash=hash_password(password),
        major=major or "",
        grade=grade or "",
        interests=interests or "",
    )
    db.session.add(user)
    db.session.commit()
    token = create_token(user.username)
    return {"success": True, "user": user, "token": token}


def authenticate_user(username: str, password: str) -> dict:
    """登录验证，返回 {success, user, token, error}"""
    user = db.session.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return {"success": False, "error": "用户名或密码错误。"}

    token = create_token(user.username)
    return {"success": True, "user": user, "token": token}


def get_user_by_token(token: str):
    """通过 Token 获取用户对象"""
    username = decode_token(token)
    if not username:
        return None
    return db.session.query(User).filter(User.username == username).first()
