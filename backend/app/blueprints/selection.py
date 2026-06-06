"""
选课蓝图 — Blueprint Pattern

处理选课、退课、查看已选课程。
使用 @login_required（Proxy Pattern）保护所有接口。
使用 Strategy Pattern 处理不同课程类型的选课规则。
"""

from flask import Blueprint, request, g
from ..decorators import login_required, log_request
from ..services import selection_service
from ..utils.response import ApiResponse
from ..utils.validators import validate_required

selection_bp = Blueprint("selection", __name__, url_prefix="/api/selection")


@selection_bp.route("/", methods=["GET"])
@login_required
@log_request
def list_selections():
    """获取当前用户的已选课程"""
    courses = selection_service.get_user_selections(g.current_user.id)
    return ApiResponse.success([c.to_dict() for c in courses])


@selection_bp.route("/", methods=["POST"])
@login_required
@log_request
def enroll():
    """批量选课 — 使用 Strategy Pattern 根据课程类型选择策略"""
    data = request.get_json(silent=True) or {}
    course_ids = data.get("courseIds") or data.get("course_ids") or []
    if not course_ids:
        return ApiResponse.error("请提交选课课程 ID 列表。")

    result = selection_service.enroll_courses(g.current_user, course_ids)
    if not result["success"]:
        return ApiResponse.error(result["error"])

    return ApiResponse.success([c.to_dict() for c in result["courses"]])


@selection_bp.route("/<int:course_id>", methods=["DELETE"])
@login_required
@log_request
def drop(course_id: int):
    """退课"""
    result = selection_service.drop_course(g.current_user.id, course_id)
    if not result["success"]:
        return ApiResponse.error(result["error"], 404)

    return ApiResponse.success([c.to_dict() for c in result["courses"]])
