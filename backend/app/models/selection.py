"""选课记录模型"""

from datetime import datetime
from ..extensions import db


class Selection(db.Model):
    __tablename__ = "selections"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="selections")
    course = db.relationship("Course", back_populates="selections")

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_user_course"),)

    def to_dict(self):
        return {
            "id": self.id,
            "course": self.course.to_dict() if self.course else None,
        }
