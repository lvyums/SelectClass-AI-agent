"""
统一响应封装 — Template Method Pattern

定义接口响应的标准模板，所有接口遵循同一响应格式：
{ "code": int, "message": str, "data": any }
"""

from flask import jsonify


class ApiResponse:
    """统一 API 响应模板"""

    @staticmethod
    def success(data=None, message="success", code=200):
        """成功响应模板"""
        return jsonify({"code": code, "message": message, "data": data}), code

    @staticmethod
    def error(message="error", code=400, data=None):
        """错误响应模板"""
        return jsonify({"code": code, "message": message, "data": data}), code

    @staticmethod
    def unauthorized(message="未授权，请先登录"):
        """401 响应模板"""
        return ApiResponse.error(message, 401)

    @staticmethod
    def forbidden(message="权限不足"):
        """403 响应模板"""
        return ApiResponse.error(message, 403)

    @staticmethod
    def not_found(message="资源未找到"):
        """404 响应模板"""
        return ApiResponse.error(message, 404)

    @staticmethod
    def too_many(message="请求过于频繁，请稍后再试"):
        """429 响应模板"""
        return ApiResponse.error(message, 429)
