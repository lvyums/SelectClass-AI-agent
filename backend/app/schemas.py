from datetime import datetime
from typing import Any, List, Optional
try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - fallback for environments without pydantic
    from typing import Any

    class Field:  # minimal fallback for editor/static analysis
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class BaseModel:  # minimal fallback to allow imports when pydantic isn't installed
        def __init__(self, **data: Any) -> None:
            for k, v in data.items():
                setattr(self, k, v)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(Token):
    user: "UserRead"


class UserResponse(BaseModel):
    user: "UserRead"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    major: Optional[str] = Field(default="", max_length=100)
    grade: Optional[str] = Field(default="", max_length=50)
    interests: Optional[str] = Field(default="", max_length=500)


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    major: Optional[str] = ""
    grade: Optional[str] = ""
    interests: Optional[str] = ""

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    major: str = Field(..., min_length=1, max_length=100)
    grade: str = Field(..., min_length=1, max_length=50)
    interests: Optional[str] = Field(default="", max_length=500)


class ScheduleItem(BaseModel):
    day: str
    slot: int
    code: int


class CourseRead(BaseModel):
    id: int
    code: str
    title: str
    faculty: str
    course_type: str
    instructor: str
    level: str
    credits: int
    summary: Optional[str] = ""
    objectives: Optional[str] = ""
    difficulty: int
    schedule_display: Optional[str] = ""
    schedule_json: Optional[List[ScheduleItem]] = []
    keywords: Optional[str] = ""

    model_config = {"from_attributes": True}


class RecommendationRequest(BaseModel):
    query: Optional[str] = Field(default="", max_length=500)


class RecommendationResponse(BaseModel):
    recommendations: List[CourseRead]
    explanation: str


class EnrollRequest(BaseModel):
    course_ids: List[int] = Field(..., alias="courseIds")

    model_config = {"populate_by_name": True}


class SelectionRead(BaseModel):
    id: int
    course: CourseRead

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    selected_courses: Optional[List[CourseRead]] = None
    recommendations: Optional[List[CourseRead]] = None
