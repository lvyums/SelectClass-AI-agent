"""用户模型"""

from datetime import datetime, timezone
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    major = db.Column(db.String(100), default="")
    grade = db.Column(db.String(50), default="")
    interests = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    selections = db.relationship("Selection", back_populates="user", cascade="all, delete-orphan")
    history = db.relationship("UserHistory", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "major": self.major,
            "grade": self.grade,
            "interests": self.interests,
        }
