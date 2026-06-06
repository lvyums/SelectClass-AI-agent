"""
课程服务 — 封装课程查询逻辑
"""

from ..extensions import db
from ..models.course import Course


def list_courses(faculty: str = None, course_type: str = None, level: str = None) -> list[Course]:
    """查询课程列表，支持可选筛选"""
    query = db.session.query(Course)
    if faculty and faculty != "All":
        query = query.filter(Course.faculty == faculty)
    if course_type and course_type != "All":
        query = query.filter(Course.course_type == course_type)
    if level and level != "All":
        query = query.filter(Course.level == level)
    return query.order_by(Course.faculty, Course.code).all()


def get_course_by_id(course_id: int) -> Course | None:
    """按 ID 查询单个课程"""
    return db.session.query(Course).filter(Course.id == course_id).first()
