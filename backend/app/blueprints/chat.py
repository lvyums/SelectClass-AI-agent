"""
智能助手蓝图 — Blueprint Pattern

处理与 AI 选课助手的对话。
"""

from flask import Blueprint, request, g
from ..decorators import login_required, log_request
from ..services.agent_service import agent
from ..utils.response import ApiResponse
from ..utils.validators import validate_required

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

MAX_HISTORY = 20
_histories: dict[int, list[dict[str, str]]] = {}


@chat_bp.route("/", methods=["POST"])
@login_required
@log_request
def chat():
    """发送消息给智能选课助手"""
    data = request.get_json(silent=True) or {}
    error = validate_required(data, ["message"])
    if error:
        return ApiResponse.error(error)

    message = data["message"][:1000]
    user = g.current_user

    history = _histories.get(user.id, [])
    history.append({"role": "user", "content": message})

    try:
        result = agent.handle_message(user, message, history)
    except Exception:
        return ApiResponse.error("智能助理暂时不可用，请稍后再试。", 500)

    answer = result.get("answer", "")
    history.append({"role": "assistant", "content": answer})
    _histories[user.id] = history[-MAX_HISTORY:]

    response_data = {"answer": answer}
    if result.get("selected_courses"):
        response_data["selected_courses"] = [c.to_dict() for c in result["selected_courses"]]
    if result.get("recommendations"):
        response_data["recommendations"] = result["recommendations"]

    return ApiResponse.success(response_data)
