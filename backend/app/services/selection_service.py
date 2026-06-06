"""
选课服务 — Strategy Pattern

通过策略模式处理不同课程类型的选课逻辑。
每种课程类型对应一个独立的选课策略，便于扩展新的选课规则。
"""

from abc import ABC, abstractmethod
from ..extensions import db
from ..models.course import Course
from ..models.selection import Selection
from ..models.history import UserHistory
from .conflict import find_conflict


# ---------------------------------------------------------------------------
# 策略抽象基类 — Strategy Pattern
# ---------------------------------------------------------------------------

class EnrollmentStrategy(ABC):
    """选课策略抽象接口"""

    @abstractmethod
    def validate(self, user, course: Course, existing_courses: list[Course]) -> str | None:
        """校验选课条件，返回错误信息或 None"""
        pass

    @abstractmethod
    def execute(self, user_id: int, course: Course) -> None:
        """执行选课操作"""
        pass


# ---------------------------------------------------------------------------
# 具体策略实现
# ---------------------------------------------------------------------------

class MajorCourseStrategy(EnrollmentStrategy):
    """专业课选课策略 — 无额外限制"""

    def validate(self, user, course: Course, existing_courses: list[Course]) -> str | None:
        existing_ids = {c.id for c in existing_courses}
        if course.id in existing_ids:
            return f"你已经选了 {course.code}，不需要重复添加"
        conflict = find_conflict(existing_courses, [course])
        if conflict:
            return f"课程 {course.code} 与已选课程 {conflict.code} 存在时间冲突"
        return None

    def execute(self, user_id: int, course: Course) -> None:
        db.session.add(Selection(user_id=user_id, course_id=course.id))


class GeneralCourseStrategy(EnrollmentStrategy):
    """公共课选课策略 — 限制选课数量"""

    MAX_GENERAL_COURSES = 5

    def validate(self, user, course: Course, existing_courses: list[Course]) -> str | None:
        existing_ids = {c.id for c in existing_courses}
        if course.id in existing_ids:
            return f"你已经选了 {course.code}，不需要重复添加"
        conflict = find_conflict(existing_courses, [course])
        if conflict:
            return f"课程 {course.code} 与已选课程 {conflict.code} 存在时间冲突"
        general_count = sum(1 for c in existing_courses if c.course_type == "公共课")
        if general_count >= self.MAX_GENERAL_COURSES:
            return f"公共课最多选 {self.MAX_GENERAL_COURSES} 门"
        return None

    def execute(self, user_id: int, course: Course) -> None:
        db.session.add(Selection(user_id=user_id, course_id=course.id))


class ElectiveCourseStrategy(EnrollmentStrategy):
    """选修课选课策略 — 默认策略，无额外限制"""

    def validate(self, user, course: Course, existing_courses: list[Course]) -> str | None:
        existing_ids = {c.id for c in existing_courses}
        if course.id in existing_ids:
            return f"你已经选了 {course.code}，不需要重复添加"
        conflict = find_conflict(existing_courses, [course])
        if conflict:
            return f"课程 {course.code} 与已选课程 {conflict.code} 存在时间冲突"
        return None

    def execute(self, user_id: int, course: Course) -> None:
        db.session.add(Selection(user_id=user_id, course_id=course.id))


# ---------------------------------------------------------------------------
# 策略注册表
# ---------------------------------------------------------------------------

_strategies: dict[str, EnrollmentStrategy] = {
    "专业课": MajorCourseStrategy(),
    "公共课": GeneralCourseStrategy(),
}

_default_strategy = ElectiveCourseStrategy()


def _get_strategy(course_type: str) -> EnrollmentStrategy:
    """根据课程类型获取对应的选课策略"""
    return _strategies.get(course_type, _default_strategy)


# ---------------------------------------------------------------------------
# 选课服务主逻辑
# ---------------------------------------------------------------------------

def get_user_selections(user_id: int) -> list[Course]:
    """获取用户已选课程列表"""
    return (
        db.session.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == user_id)
        .order_by(Course.faculty, Course.code)
        .all()
    )


def enroll_courses(user, course_ids: list[int]) -> dict:
    """
    批量选课 — 使用策略模式

    返回 {success, courses, error}
    """
    if not course_ids:
        return {"success": False, "error": "请提交选课课程 ID 列表。"}

    existing_courses = get_user_selections(user.id)
    requested_courses = db.session.query(Course).filter(Course.id.in_(course_ids)).all()

    # 检查是否有不存在的课程 ID
    found_ids = {c.id for c in requested_courses}
    missing_ids = [cid for cid in course_ids if cid not in found_ids]
    if missing_ids:
        return {"success": False, "error": f"以下课程 ID 不存在：{missing_ids}"}

    for course in requested_courses:
        strategy = _get_strategy(course.course_type)
        error = strategy.validate(user, course, existing_courses)
        if error:
            return {"success": False, "error": error}
        strategy.execute(user.id, course)
        existing_courses.append(course)

    # 记录历史
    db.session.add(UserHistory(user_id=user.id, event_type="enroll", payload={"course_ids": course_ids}))
    db.session.commit()

    return {"success": True, "courses": get_user_selections(user.id)}


def drop_course(user_id: int, course_id: int) -> dict:
    """
    退课

    返回 {success, courses, error}
    """
    selection = (
        db.session.query(Selection)
        .filter(Selection.user_id == user_id, Selection.course_id == course_id)
        .first()
    )
    if not selection:
        return {"success": False, "error": "未找到该选课记录。"}

    db.session.delete(selection)
    db.session.add(UserHistory(user_id=user_id, event_type="drop", payload={"course_id": course_id}))
    db.session.commit()

    return {"success": True, "courses": get_user_selections(user_id)}
