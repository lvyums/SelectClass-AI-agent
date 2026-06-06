"""
推荐服务 — 基于评分算法的课程推荐

评分维度：查询匹配、专业匹配、年级匹配、兴趣匹配、学分、难度。
可选调用 MiMo LLM 生成推荐解释。
"""

import logging
from ..extensions import db
from ..models.course import Course
from ..models.history import UserHistory

logger = logging.getLogger(__name__)


def _course_score(course: Course, query_text: str, user_major: str, user_grade: str, user_interests: str) -> int:
    """计算课程推荐分数"""
    score = 0
    course_text = " ".join([
        course.title, course.code, course.summary or "",
        course.faculty, course.course_type, course.instructor,
        course.keywords or "",
    ]).lower()

    # 查询匹配
    if query_text and query_text in course_text:
        score += 30

    # 专业匹配（课程院系或关键词包含用户专业）
    if user_major and user_major in course_text:
        score += 20

    # 年级匹配（课程级别与年级对应）
    if user_grade:
        grade_level_map = {"大一": "beginner", "大二": "beginner", "大三": "intermediate", "大四": "advanced"}
        expected_level = grade_level_map.get(user_grade, "")
        if expected_level and expected_level in (course.level or "").lower():
            score += 10

    # 兴趣匹配（用户兴趣关键词出现在课程文本中）
    if user_interests:
        score += sum(5 for keyword in user_interests.lower().split() if keyword in course_text)

    # 学分和难度调整
    score += course.credits
    score += max(0, 5 - course.difficulty)
    return score


def recommend_courses(user, query: str = "", limit: int = 8) -> list[Course]:
    """获取推荐课程列表"""
    query_text = query.strip().lower()
    courses = db.session.query(Course).all()
    scored = [
        (course, _course_score(course, query_text, user.major or "", user.grade or "", user.interests or ""))
        for course in courses
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    recommendations = [course for course, _ in scored[:limit]]

    # 可选：调用 LLM 生成推荐解释
    from flask import current_app
    if current_app.config.get("MIMO_API_KEY"):
        try:
            from .mimo_client import load_mimo
            mimo = load_mimo()
            prompt = _build_recommendation_prompt(recommendations, user, query)
            answer = mimo([{"role": "user", "content": prompt}], max_tokens=512)
            db.session.add(UserHistory(
                user_id=user.id, event_type="recommendation_prompt",
                payload={"query": query, "result": answer},
            ))
            db.session.commit()
        except Exception as e:
            logger.warning("推荐 LLM 解释生成失败: %s", e)

    return recommendations


def _sanitize_for_prompt(value: str, max_len: int = 100) -> str:
    """清理用户输入，防止 prompt 注入"""
    if not value:
        return ""
    cleaned = value.replace("{", "").replace("}", "").replace("\\", "")
    cleaned = cleaned.replace("\n", " ").replace("\r", "")
    return cleaned[:max_len].strip()


def _build_recommendation_prompt(recommendations: list, user, query: str) -> str:
    """构建推荐解释的 LLM 提示词"""
    lines = [
        f"学生专业: {_sanitize_for_prompt(user.major, 50)}",
        f"学生年级: {_sanitize_for_prompt(user.grade, 20)}",
        f"学生兴趣: {_sanitize_for_prompt(user.interests, 100)}",
        f"查询: {_sanitize_for_prompt(query, 200)}",
        "以下为备选课程，请按照匹配度排序并返回简短说明：",
    ]
    for course in recommendations:
        lines.append(f"- {course.code} {course.title} ({course.faculty})：{course.summary}")
    return "\n".join(lines)
