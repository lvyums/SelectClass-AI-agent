"""
推荐蓝图 — Blueprint Pattern

提供个性化课程推荐。
"""

from flask import Blueprint, request, g
from ..decorators import login_required, log_request
from ..services.recommendation_service import recommend_courses
from ..utils.response import ApiResponse

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


@recommendations_bp.route("/", methods=["POST"])
@login_required
@log_request
def recommend():
    """获取个性化课程推荐"""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")

    recs = recommend_courses(g.current_user, query)
    explanation = (
        f"已根据你的专业和年级推荐课程，并结合关键词"{query}"。"
        if query else "已根据你的专业和年级推荐这些课程。"
    )
    return ApiResponse.success({
        "recommendations": [c.to_dict() for c in recs],
        "explanation": explanation,
    })
