# pyright: reportMissingImports=false
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, UniqueConstraint, TIMESTAMP
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    major = Column(String(100), default="")
    grade = Column(String(50), default="")
    interests = Column(Text, default="")
    created_at = Column(TIMESTAMP, server_default=func.now())

    selections = relationship("Selection", back_populates="user", cascade="all, delete-orphan")
    history = relationship("UserHistory", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    faculty = Column(String(128), nullable=False)
    course_type = Column(String(64), nullable=False)
    instructor = Column(String(128), nullable=False)
    level = Column(String(64), nullable=False)
    credits = Column(Integer, nullable=False)
    summary = Column(Text)
    objectives = Column(Text)
    difficulty = Column(Integer, nullable=False)
    schedule_display = Column(String(255))
    schedule_json = Column(JSON)
    keywords = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    selections = relationship("Selection", back_populates="course")

    __table_args__ = (UniqueConstraint("code", name="uq_course_code"),)


class Selection(Base):
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="selections")
    course = relationship("Course", back_populates="selections")

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_user_course"),)


class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="history")
