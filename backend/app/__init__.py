"""
Flask 应用工厂 — Factory Pattern

create_app() 函数封装应用创建的全部流程：
1. 加载配置（Singleton Pattern）
2. 初始化扩展（db、cors）
3. 注册蓝图（Blueprint Pattern）
4. 注册错误处理器
5. 创建数据库表

使用工厂模式解耦应用创建与配置，支持多环境切换。
"""

import time
import logging
from flask import Flask
from .config import config
from .extensions import db, cors

logger = logging.getLogger(__name__)


def create_app(config_name: str = "default") -> Flask:
    """
    Flask 应用工厂 — Factory Pattern

    Args:
        config_name: 配置名称 ('development', 'testing', 'production', 'default')

    Returns:
        配置完成的 Flask 应用实例
    """
    app = Flask(__name__)

    # 1. 加载配置（Singleton Pattern — 配置全局唯一）
    app.config.from_object(config[config_name])
    app.config["SQLALCHEMY_DATABASE_URI"] = config[config_name]().SQLALCHEMY_DATABASE_URI

    # 2. 初始化扩展（Singleton Pattern — db 全局唯一）
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", [])}})

    # 3. 注册蓝图（Blueprint Pattern — 路由模块化）
    _register_blueprints(app)

    # 4. 注册错误处理器
    _register_error_handlers(app)

    # 5. 创建数据库表
    with app.app_context():
        from . import models  # noqa: F401 — 确保模型被导入
        db.create_all()
        logger.info("数据库表已创建/确认存在")

    logger.info("Flask 应用创建完成 (config=%s)", config_name)
    return app


def _register_blueprints(app: Flask):
    """注册所有蓝图 — Blueprint Pattern"""
    from .blueprints import (
        auth_bp, courses_bp, selection_bp,
        profile_bp, recommendations_bp, chat_bp,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(selection_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(chat_bp)

    # 健康检查
    @app.route("/health")
    def health():
        return {"status": "ok", "backend": "flask", "timestamp": time.time()}

    logger.info("蓝图注册完成")


def _register_error_handlers(app: Flask):
    """注册全局错误处理器"""
    from .utils.response import ApiResponse

    @app.errorhandler(404)
    def not_found(e):
        return ApiResponse.not_found("请求的资源不存在")

    @app.errorhandler(405)
    def method_not_allowed(e):
        return ApiResponse.error("请求方法不允许", 405)

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("服务器内部错误: %s", e)
        return ApiResponse.error("服务器内部错误", 500)
