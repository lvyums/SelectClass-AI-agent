from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_db, get_current_user
from ..models import Course, Selection, UserHistory
from ..schemas import EnrollRequest, CourseRead
from ..services.conflict import find_conflict

router = APIRouter(prefix="/selection", tags=["selection"])


@router.get("/", response_model=List[CourseRead])
def list_selection(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    selection_courses = (
        db.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == current_user.id)
        .order_by(Course.faculty, Course.code)
        .all()
    )
    return selection_courses


@router.post("/", response_model=List[CourseRead])
def enroll(request: EnrollRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    course_ids = request.course_ids
    if not course_ids:
        raise HTTPException(status_code=400, detail="请提交选课课程 ID 列表。")

    existing_courses = (
        db.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == current_user.id)
        .all()
    )
    requested_courses = db.query(Course).filter(Course.id.in_(course_ids)).all()

    current_ids = {course.id for course in existing_courses}
    new_courses = [course for course in requested_courses if course.id not in current_ids]

    conflict = find_conflict(existing_courses, new_courses)
    if conflict:
        raise HTTPException(status_code=400, detail=f"课程 {conflict.code} 与已有选课冲突。")

    for course in new_courses:
        db.add(Selection(user_id=current_user.id, course_id=course.id))

    activity = UserHistory(
        user_id=current_user.id,
        event_type="enroll",
        payload={"course_ids": course_ids},
    )
    db.add(activity)
    db.commit()

    selected_courses = (
        db.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == current_user.id)
        .order_by(Course.faculty, Course.code)
        .all()
    )
    return selected_courses


@router.delete("/{course_id}", response_model=List[CourseRead])
def drop_course(course_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    selection = (
        db.query(Selection)
        .filter(Selection.user_id == current_user.id, Selection.course_id == course_id)
        .first()
    )
    if not selection:
        raise HTTPException(status_code=404, detail="未找到该选课记录。")

    db.delete(selection)

    activity = UserHistory(
        user_id=current_user.id,
        event_type="drop",
        payload={"course_id": course_id},
    )
    db.add(activity)
    db.commit()

    selected_courses = (
        db.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == current_user.id)
        .order_by(Course.faculty, Course.code)
        .all()
    )
    return selected_courses
