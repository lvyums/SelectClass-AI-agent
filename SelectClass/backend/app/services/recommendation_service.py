from sqlalchemy.orm import Session
from .mimo_client import load_mimo
from ..core.config import settings
from ..models import Course, UserHistory


def _course_score(course: Course, query_text: str, user_major: str, user_grade: str, user_interests: str) -> int:
    score = 0
    text = " ".join([
        course.title,
        course.code,
        course.summary or "",
        course.faculty,
        course.course_type,
        course.instructor,
        course.keywords or "",
        user_major,
        user_grade,
        user_interests,
        query_text,
    ]).lower()
    if query_text and query_text.lower() in text:
        score += 30
    if user_major and user_major.lower() in text:
        score += 20
    if user_grade and user_grade.lower() in text:
        score += 10
    if user_interests:
        score += sum(5 for keyword in user_interests.lower().split() if keyword in text)
    score += course.credits
    score += max(0, 5 - course.difficulty)
    return score


def recommend_courses(db: Session, user, query: str = "", limit: int = 8):
    query_text = query.strip().lower()
    courses = db.query(Course).all()
    scored = [
        (course, _course_score(course, query_text, user.major or "", user.grade or "", user.interests or ""))
        for course in courses
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    recommendations = [course for course, _ in scored[:limit]]

    if settings.mimo_api_key:
        try:
            mimo = load_mimo()
            prompt = _build_recommendation_prompt(recommendations, user, query)
            answer = mimo(prompt)
            user_history = UserHistory(user_id=user.id, event_type="recommendation_prompt", payload={"query": query, "result": answer})
            db.add(user_history)
            db.commit()
        except Exception:
            pass

    return recommendations


def _build_recommendation_prompt(recommendations, user, query):
    lines = [
        f"学生专业: {user.major}",
        f"学生年级: {user.grade}",
        f"学生兴趣: {user.interests}",
        f"查询: {query}",
        "以下为备选课程，请按照匹配度排序并返回简短说明：",
    ]
    for course in recommendations:
        lines.append(f"- {course.code} {course.title} ({course.faculty})：{course.summary}")
    return "\n".join(lines)
