"""
个人资料蓝图 — Blueprint Pattern

处理用户资料更新。
"""

from flask import Blueprint, request, g
from ..decorators import login_required, log_request
from ..extensions import db
from ..utils.response import ApiResponse
from ..utils.validators import validate_required

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@profile_bp.route("/", methods=["POST"])
@login_required
@log_request
def update_profile():
    """更新用户专业、年级、兴趣"""
    data = request.get_json(silent=True) or {}
    error = validate_required(data, ["major", "grade"])
    if error:
        return ApiResponse.error(error)

    user = g.current_user
    user.major = data["major"]
    user.grade = data["grade"]
    user.interests = data.get("interests", "")
    db.session.commit()

    return ApiResponse.success(user.to_dict())
