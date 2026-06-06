from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.security import get_db, get_current_user
from ..schemas import RecommendationRequest, RecommendationResponse
from ..services.recommendation_service import recommend_courses

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    recommendations = recommend_courses(db, current_user, request.query or "")
    explanation = (
        f"已根据你的专业和年级推荐课程，并结合关键词“{request.query}”。" if request.query else "已根据你的专业和年级推荐这些课程。"
    )
    return {"recommendations": recommendations, "explanation": explanation}
