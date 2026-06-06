"""
课程数据导入脚本

使用 Flask 应用上下文导入 courses.json 中的课程数据。
"""

import json
import sys
from pathlib import Path

from sqlalchemy.exc import IntegrityError

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.course import Course


def load_courses() -> list[dict]:
    data_file = ROOT_DIR / "data" / "courses.json"
    with open(data_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    app = create_app("default")
    with app.app_context():
        courses = load_courses()
        for entry in courses:
            course = Course(
                code=entry["code"],
                title=entry["title"],
                faculty=entry["faculty"],
                course_type=entry["course_type"],
                instructor=entry["instructor"],
                level=entry["level"],
                credits=entry["credits"],
                summary=entry.get("summary", ""),
                objectives=entry.get("objectives", ""),
                difficulty=entry.get("difficulty", 1),
                schedule_display=entry.get("schedule_display", ""),
                schedule_json=entry.get("schedule_json", []),
                keywords=entry.get("keywords", ""),
            )
            db.session.add(course)
            try:
                db.session.commit()
                print(f"已导入课程：{course.code}")
            except IntegrityError:
                db.session.rollback()
                print(f"跳过已存在课程：{course.code}")


if __name__ == "__main__":
    main()
