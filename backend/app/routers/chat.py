from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_db, get_current_user
from ..schemas import ChatRequest, ChatResponse
from ..models import User
from ..services.agent_service import agent

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_HISTORY = 20
_histories: dict[int, list[dict[str, str]]] = {}


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = _histories.get(current_user.id, [])
    history.append({"role": "user", "content": request.message})

    try:
        result = agent.handle_message(db, current_user, request.message, history)
    except Exception:
        raise HTTPException(status_code=500, detail="智能助理暂时不可用，请稍后再试。")

    answer = result.get("answer", "")
    history.append({"role": "assistant", "content": answer})
    _histories[current_user.id] = history[-MAX_HISTORY:]

    return ChatResponse(
        answer=answer,
        selected_courses=result.get("selected_courses"),
        recommendations=result.get("recommendations"),
    )
