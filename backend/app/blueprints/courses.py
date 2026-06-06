"""
课程蓝图 — Blueprint Pattern

提供课程列表查询和课程详情查询。
"""

from flask import Blueprint, request
from ..decorators import log_request
from ..services import course_service
from ..utils.response import ApiResponse

courses_bp = Blueprint("courses", __name__, url_prefix="/api/courses")


@courses_bp.route("/", methods=["GET"])
@log_request
def list_courses():
    """获取课程列表，支持按院系、类型、难度筛选"""
    faculty = request.args.get("faculty")
    course_type = request.args.get("course_type")
    level = request.args.get("level")

    courses = course_service.list_courses(faculty, course_type, level)
    return ApiResponse.success([c.to_dict() for c in courses])


@courses_bp.route("/<int:course_id>", methods=["GET"])
@log_request
def get_course(course_id: int):
    """获取单个课程详情"""
    course = course_service.get_course_by_id(course_id)
    if not course:
        return ApiResponse.not_found("课程未找到")
    return ApiResponse.success(course.to_dict())
