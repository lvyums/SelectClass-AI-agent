from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_db
from ..models import Course
from ..schemas import CourseRead

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=List[CourseRead])
def list_courses(
    faculty: Optional[str] = None,
    course_type: Optional[str] = None,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Course)
    if faculty and faculty != "All":
        query = query.filter(Course.faculty == faculty)
    if course_type and course_type != "All":
        query = query.filter(Course.course_type == course_type)
    if level and level != "All":
        query = query.filter(Course.level == level)
    return query.order_by(Course.faculty, Course.code).all()


@router.get("/{course_id}", response_model=CourseRead)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程未找到。")
    return course
