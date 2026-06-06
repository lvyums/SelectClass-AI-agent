from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import get_db, get_current_user
from ..models import User
from ..schemas import ProfileUpdate, UserRead

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/", response_model=UserRead)
def update_profile(profile: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.major = profile.major
    current_user.grade = profile.grade
    current_user.interests = profile.interests or ""
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
