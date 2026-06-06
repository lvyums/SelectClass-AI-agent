"""
冲突检测服务 — 检查课程时间冲突
"""

from typing import List, Set
from ..models.course import Course


def extract_schedule_codes(course: Course) -> Set[int]:
    """提取课程的时间槽编码"""
    schedule = course.schedule_json or []
    return {item.get("code") for item in schedule if item and isinstance(item.get("code"), int)}


def find_conflict(existing: List[Course], requested: List[Course]) -> Course | None:
    """检测已选课程与待选课程之间的时间冲突，返回第一个冲突的课程或 None"""
    used_codes: Set[int] = set()
    for course in existing:
        used_codes.update(extract_schedule_codes(course))

    for course in requested:
        if extract_schedule_codes(course) & used_codes:
            return course
        used_codes.update(extract_schedule_codes(course))
    return None
