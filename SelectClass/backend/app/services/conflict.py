from typing import List, Set

from ..models import Course


def extract_schedule_codes(course: Course) -> Set[int]:
    schedule = course.schedule_json or []
    return {item.get("code") for item in schedule if item and isinstance(item.get("code"), int)}


def find_conflict(existing: List[Course], requested: List[Course]) -> Course | None:
    used_codes: Set[int] = set()
    for course in existing:
        used_codes.update(extract_schedule_codes(course))

    for course in requested:
        if extract_schedule_codes(course) & used_codes:
            return course
        used_codes.update(extract_schedule_codes(course))
    return None
