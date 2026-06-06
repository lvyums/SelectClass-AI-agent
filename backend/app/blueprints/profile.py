"""
个人资料蓝图 — Blueprint Pattern

处理用户资料更新。
"""

from flask import Blueprint, request, g
from ..decorators import login_required, log_request
from ..extensions import db
from ..utils.response import ApiResponse
from ..utils.validators import validate_required, validate_length

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@profile_bp.route("/", methods=["PUT"])
@login_required
@log_request
def update_profile():
    """更新用户专业、年级、兴趣"""
    data = request.get_json(silent=True) or {}
    error = validate_required(data, ["major", "grade"])
    if error:
        return ApiResponse.error(error)

    error = validate_length(data["major"], "专业", min_len=1, max_len=100)
    if error:
        return ApiResponse.error(error)
    error = validate_length(data["grade"], "年级", min_len=1, max_len=50)
    if error:
        return ApiResponse.error(error)
    interests = data.get("interests", "")
    if interests:
        error = validate_length(interests, "兴趣", max_len=500)
        if error:
            return ApiResponse.error(error)

    user = g.current_user
    user.major = data["major"].strip()
    user.grade = data["grade"].strip()
    user.interests = interests.strip()
    db.session.commit()

    return ApiResponse.success(user.to_dict())
