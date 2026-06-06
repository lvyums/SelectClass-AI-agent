"""课程模型"""

from datetime import datetime
from ..extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String(50), nullable=False, index=True, unique=True)
    title = db.Column(db.String(255), nullable=False)
    faculty = db.Column(db.String(128), nullable=False)
    course_type = db.Column(db.String(64), nullable=False)
    instructor = db.Column(db.String(128), nullable=False)
    level = db.Column(db.String(64), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    summary = db.Column(db.Text)
    objectives = db.Column(db.Text)
    difficulty = db.Column(db.Integer, nullable=False)
    schedule_display = db.Column(db.String(255))
    schedule_json = db.Column(db.JSON)
    keywords = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    selections = db.relationship("Selection", back_populates="course")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "faculty": self.faculty,
            "course_type": self.course_type,
            "instructor": self.instructor,
            "level": self.level,
            "credits": self.credits,
            "summary": self.summary or "",
            "objectives": self.objectives or "",
            "difficulty": self.difficulty,
            "schedule_display": self.schedule_display or "",
            "schedule_json": self.schedule_json or [],
            "keywords": self.keywords or "",
        }
