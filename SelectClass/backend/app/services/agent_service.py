import json
import logging
import re
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Course, Selection, User, UserHistory
from .conflict import find_conflict
from .mimo_client import load_mimo, _extract_all_blocks

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """你是小选，大学选课助手。和学生 {username} 聊天。

学生：{major} {grade}，兴趣：{interests}
已选课程：{current_selections}

你可以调用以下工具：
- search_courses(keyword): 按关键词搜索课程，返回课程列表（含 id、code、title 等）
- get_selections(): 查看已选课程
- add_course(course_id): 将课程加入选课列表，course_id 必须是 search_courses 返回的数字 id
- remove_course(course_id): 退选课程
- replace_course(old_course_id, new_course_id): 换课
- recommend_courses(query): 推荐课程

规则：
- 用户提到课程名/代号时，必须调用 search_courses 搜索，不要自己猜测
- 搜索到结果后，如果用户已确认选课，直接调用 add_course(course_id) 添加
- course_id 必须用 search_courses 返回的数字 id，禁止猜测
- 只输出 JSON，不要输出其他任何文字"""

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "search_courses",
        "description": "按关键词搜索课程。支持课程名、课程代号、教师名、院系名搜索。返回匹配的课程列表，包含课程 ID、代号、名称、学分、教师、时间等信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，如 '英语'、'CS101'、'张教授'、'数学学院'"
                }
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "get_selections",
        "description": "查看学生当前已选的全部课程列表。无需参数。",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "add_course",
        "description": "将一门课程加入学生的选课列表。会自动检测时间冲突。需要先通过 search_courses 获取课程 ID。",
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {"type": "integer", "description": "课程的数字 ID，从 search_courses 结果中获取"}
            },
            "required": ["course_id"]
        }
    },
    {
        "name": "remove_course",
        "description": "从学生选课列表中移除一门课程。需要先通过 get_selections 获取课程 ID。",
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {"type": "integer", "description": "要移除的课程 ID"}
            },
            "required": ["course_id"]
        }
    },
    {
        "name": "replace_course",
        "description": "将一门已选课程替换为另一门新课程。会自动检测新课程是否与其他已选课程冲突。",
        "parameters": {
            "type": "object",
            "properties": {
                "old_course_id": {"type": "integer", "description": "要换掉的已选课程 ID"},
                "new_course_id": {"type": "integer", "description": "要换入的新课程 ID"}
            },
            "required": ["old_course_id", "new_course_id"]
        }
    },
    {
        "name": "recommend_courses",
        "description": "根据学生的专业、年级和兴趣推荐课程。可以传入具体方向关键词。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "推荐方向关键词，如 '人工智能'、'数据科学'，或空字符串表示通用推荐"}
            }
        }
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def _exec_search_courses(db: Session, keyword: str) -> dict:
    kw = keyword.strip()
    if not kw:
        return {"courses": [], "message": "请输入搜索关键词"}

    from sqlalchemy import or_

    # Try full keyword first
    conditions = [
        Course.title.contains(kw),
        Course.code.contains(kw.upper()),
        Course.instructor.contains(kw),
        Course.faculty.contains(kw),
        Course.keywords.contains(kw) if Course.keywords else False,
    ]
    courses = db.query(Course).filter(or_(*conditions)).limit(15).all()

    # If no results, try removing common suffixes like "课", "课程"
    if not courses:
        for suffix in ["课程", "课", "专业", "学院"]:
            if kw.endswith(suffix) and len(kw) > len(suffix):
                shorter = kw[:-len(suffix)]
                conditions = [
                    Course.title.contains(shorter),
                    Course.keywords.contains(shorter) if Course.keywords else False,
                    Course.faculty.contains(shorter),
                ]
                courses = db.query(Course).filter(or_(*conditions)).limit(15).all()
                if courses:
                    break

    return {
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "credits": c.credits,
                "instructor": c.instructor,
                "faculty": c.faculty,
                "level": c.level,
                "course_type": c.course_type,
                "schedule": c.schedule_display or "",
                "difficulty": c.difficulty,
                "summary": (c.summary or "")[:100],
            }
            for c in courses
        ],
        "count": len(courses),
    }


def _exec_get_selections(db: Session, user_id: int) -> dict:
    courses = (
        db.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == user_id)
        .order_by(Course.faculty, Course.code)
        .all()
    )
    total_credits = sum(c.credits for c in courses)
    return {
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "credits": c.credits,
                "instructor": c.instructor,
                "schedule": c.schedule_display or "",
            }
            for c in courses
        ],
        "count": len(courses),
        "total_credits": total_credits,
    }


def _exec_add_course(db: Session, user_id: int, course_id: int, current_courses: list[Course]) -> dict:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return {"success": False, "error": f"未找到 ID 为 {course_id} 的课程"}

    existing_ids = {c.id for c in current_courses}
    if course_id in existing_ids:
        return {"success": False, "error": f"你已经选了 {course.code} {course.title}，不需要重复添加"}

    other_courses = [c for c in current_courses if c.id != course_id]
    conflict = find_conflict(other_courses, [course])
    if conflict:
        return {
            "success": False,
            "error": f"{course.code} {course.title} 与已选的 {conflict.code} {conflict.title} 时间冲突",
            "conflict_with": {"code": conflict.code, "title": conflict.title, "id": conflict.id},
        }

    db.add(Selection(user_id=user_id, course_id=course_id))
    db.commit()
    return {"success": True, "course": {"id": course.id, "code": course.code, "title": course.title, "credits": course.credits}}


def _exec_remove_course(db: Session, user_id: int, course_id: int) -> dict:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return {"success": False, "error": f"未找到 ID 为 {course_id} 的课程"}

    sel = db.query(Selection).filter(Selection.user_id == user_id, Selection.course_id == course_id).first()
    if not sel:
        return {"success": False, "error": f"你没有选 {course.code} {course.title}，无法退选"}

    db.delete(sel)
    db.commit()
    return {"success": True, "course": {"code": course.code, "title": course.title}}


def _exec_replace_course(db: Session, user_id: int, old_id: int, new_id: int, current_courses: list[Course]) -> dict:
    old_course = db.query(Course).filter(Course.id == old_id).first()
    new_course = db.query(Course).filter(Course.id == new_id).first()
    if not old_course:
        return {"success": False, "error": f"未找到 ID 为 {old_id} 的课程"}
    if not new_course:
        return {"success": False, "error": f"未找到 ID 为 {new_id} 的课程"}

    sel = db.query(Selection).filter(Selection.user_id == user_id, Selection.course_id == old_id).first()
    if not sel:
        return {"success": False, "error": f"你没有选 {old_course.code} {old_course.title}，无法替换"}

    remaining = [c for c in current_courses if c.id != old_id]
    conflict = find_conflict(remaining, [new_course])
    if conflict:
        return {
            "success": False,
            "error": f"{new_course.code} {new_course.title} 与已选的 {conflict.code} {conflict.title} 时间冲突，无法替换",
        }

    db.delete(sel)
    db.add(Selection(user_id=user_id, course_id=new_id))
    db.commit()
    return {
        "success": True,
        "removed": {"code": old_course.code, "title": old_course.title},
        "added": {"code": new_course.code, "title": new_course.title},
    }


def _exec_recommend_courses(db: Session, user: User, query: str) -> dict:
    from .recommendation_service import recommend_courses
    recs = recommend_courses(db, user, query, limit=8)
    return {
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "credits": c.credits,
                "instructor": c.instructor,
                "faculty": c.faculty,
                "level": c.level,
                "course_type": c.course_type,
                "difficulty": c.difficulty,
                "summary": (c.summary or "")[:80],
            }
            for c in recs
        ],
        "count": len(recs),
    }


TOOL_MAP = {
    "search_courses": lambda db, uid, args, cc: _exec_search_courses(db, args.get("keyword", "")),
    "get_selections": lambda db, uid, args, cc: _exec_get_selections(db, uid),
    "add_course": lambda db, uid, args, cc: _exec_add_course(db, uid, args.get("course_id"), cc),
    "remove_course": lambda db, uid, args, cc: _exec_remove_course(db, uid, args.get("course_id")),
    "replace_course": lambda db, uid, args, cc: _exec_replace_course(db, uid, args.get("old_course_id"), args.get("new_course_id"), cc),
    "recommend_courses": lambda db, uid, args, cc: _exec_recommend_courses(db, _get_user(db, uid), args.get("query", "")),
}


def _get_user(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

# ---------------------------------------------------------------------------
# Keyword fallback (degradation when LLM fails)
# ---------------------------------------------------------------------------

KEYWORD_MAP = {
    "add": ["选", "加", "选课", "想上", "报名"],
    "remove": ["退", "删", "不要", "退选", "取消"],
    "replace": ["换成", "换", "替换"],
    "list": ["选了哪些", "当前选课", "我的课", "已选", "选了什么"],
    "recommend": ["推荐", "建议", "什么课好"],
}

CONFIRM_WORDS = ["要", "好的", "可以", "行", "确认", "是", "嗯", "好", "ok", "OK", "添加", "帮我选", "选上"]


def _keyword_classify(message: str) -> str | None:
    lower = message.lower()
    for intent, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in lower:
                return intent
    return None


def _keyword_fallback(db: Session, user: User, message: str, current_courses: list[Course]) -> dict:
    intent = _keyword_classify(message)
    codes = re.findall(r"[A-Za-z]{2,}\d{2,}", message)

    if intent == "list":
        if not current_courses:
            return {"answer": "你目前还没有选修任何课程。"}
        lines = [f"- {c.code} {c.title}（{c.credits}学分）" for c in current_courses]
        total = sum(c.credits for c in current_courses)
        return {"answer": f"你当前已选 {len(current_courses)} 门课程，共 {total} 学分：\n" + "\n".join(lines)}

    if intent == "recommend":
        result = _exec_recommend_courses(db, user, message)
        if result["courses"]:
            lines = [f"- {c['code']} {c['title']}（{c['credits']}学分）" for c in result["courses"]]
            return {"answer": "为你推荐以下课程：\n" + "\n".join(lines), "recommendations": result["courses"]}
        return {"answer": "暂时没有找到合适的推荐课程。"}

    if intent == "add":
        results = []
        changed = False
        # Add by course code (e.g. CS101)
        for code in codes:
            course = db.query(Course).filter(Course.code.ilike(code)).first()
            if course:
                r = _exec_add_course(db, user.id, course.id, current_courses)
                if r["success"]:
                    current_courses.append(course)
                    changed = True
                    results.append(f"已添加 {course.code} {course.title}")
                else:
                    results.append(r["error"])
            else:
                results.append(f"未找到课程 {code}")

        # If no code found, try searching by Chinese course name
        if not codes:
            search_term = message
            for kw in ["帮我选", "帮我加", "选课", "选", "加", "想上", "报名", "添加"]:
                search_term = search_term.replace(kw, "")
            search_term = search_term.strip()
            if search_term:
                from sqlalchemy import or_
                matched = db.query(Course).filter(
                    or_(
                        Course.title.contains(search_term),
                        Course.keywords.contains(search_term),
                        Course.faculty.contains(search_term),
                    )
                ).limit(5).all()
                if len(matched) == 1:
                    r = _exec_add_course(db, user.id, matched[0].id, current_courses)
                    if r["success"]:
                        current_courses.append(matched[0])
                        changed = True
                        results.append(f"已添加 {matched[0].code} {matched[0].title}")
                    else:
                        results.append(r["error"])
                elif len(matched) > 1:
                    lines = [f"- {c.code} {c.title}（{c.credits}学分，{c.instructor}）" for c in matched]
                    return {"answer": f"找到多门相关课程，请指定：\n" + "\n".join(lines)}
                else:
                    results.append(f"未找到与「{search_term}」相关的课程")

        resp = {"answer": "。".join(results) + "。"}
        if changed:
            resp["selected_courses"] = (
                db.query(Course)
                .join(Selection, Selection.course_id == Course.id)
                .filter(Selection.user_id == user.id)
                .order_by(Course.faculty, Course.code)
                .all()
            )
        else:
            resp["selected_courses"] = current_courses if current_courses else None
        return resp

    if intent == "remove":
        results = []
        changed = False
        for code in codes:
            course = db.query(Course).filter(Course.code.ilike(code)).first()
            if course:
                r = _exec_remove_course(db, user.id, course.id)
                if r["success"]:
                    changed = True
                    results.append(f"已退选 {code}")
                else:
                    results.append(r["error"])
            else:
                results.append(f"未找到课程 {code}")

        # If no code found, try searching by Chinese course name in selections
        if not codes:
            search_term = message
            for kw in ["退掉", "退选", "取消", "删掉", "不要", "退", "删"]:
                search_term = search_term.replace(kw, "")
            search_term = search_term.strip()
            if search_term:
                selected_ids = {c.id for c in current_courses}
                matched = [c for c in current_courses if search_term in (c.title or "") or search_term in (c.keywords or "")]
                if len(matched) == 1:
                    r = _exec_remove_course(db, user.id, matched[0].id)
                    if r["success"]:
                        changed = True
                        results.append(f"已退选 {matched[0].code} {matched[0].title}")
                    else:
                        results.append(r["error"])
                elif len(matched) > 1:
                    lines = [f"- {c.code} {c.title}" for c in matched]
                    return {"answer": f"你选了多门相关课程，请指定退哪门：\n" + "\n".join(lines)}
                else:
                    results.append(f"你在已选课程中没有找到「{search_term}」")

        resp = {"answer": "。".join(results) + "。"}
        if changed:
            resp["selected_courses"] = (
                db.query(Course)
                .join(Selection, Selection.course_id == Course.id)
                .filter(Selection.user_id == user.id)
                .order_by(Course.faculty, Course.code)
                .all()
            )
        else:
            resp["selected_courses"] = current_courses if current_courses else None
        return resp

    return {"answer": "抱歉，我暂时无法理解你的请求。你可以试试：\n- 帮我选 CS101\n- 退掉数学课\n- 我选了哪些课\n- 推荐一些课"}


# ---------------------------------------------------------------------------
# Main Agent
# ---------------------------------------------------------------------------

class CourseAgent:
    def __init__(self):
        # Per-user cache of last search results for follow-up operations
        self._last_search: dict[int, list[dict]] = {}

    def handle_message(self, db: Session, user: User, message: str, history: list[dict]) -> dict:
        current_courses = (
            db.query(Course)
            .join(Selection, Selection.course_id == Course.id)
            .filter(Selection.user_id == user.id)
            .all()
        )

        # If user sends a confirmation word (e.g. "要", "好的") and we have cached search results,
        # directly add the cached course(s) without calling LLM
        if message.strip() in CONFIRM_WORDS and user.id in self._last_search:
            cached = self._last_search[user.id]
            if len(cached) == 1:
                cid = cached[0]["id"]
                r = _exec_add_course(db, user.id, cid, current_courses)
                self._last_search.pop(user.id, None)
                updated = (
                    db.query(Course)
                    .join(Selection, Selection.course_id == Course.id)
                    .filter(Selection.user_id == user.id)
                    .order_by(Course.faculty, Course.code)
                    .all()
                )
                if r.get("success"):
                    return {"answer": f"已成功添加 {r['course']['code']} {r['course']['title']}。", "selected_courses": updated}
                else:
                    return {"answer": r.get("error", "添加失败"), "selected_courses": updated}
            elif len(cached) > 1:
                lines = [f"- {c['code']} {c['title']}（{c['credits']}学分）" for c in cached]
                return {"answer": f"请指定你要选哪门课（输入课程代号）：\n" + "\n".join(lines)}

        # Build system prompt
        system_prompt = self._build_system_prompt(user, current_courses)

        # Build messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        # Inject recent search context so LLM knows course IDs from previous searches
        if user.id in self._last_search and self._last_search[user.id]:
            cached = self._last_search[user.id]
            cache_summary = ", ".join(f"{c['code']}(ID:{c['id']})" for c in cached[:5])
            messages.append({
                "role": "user",
                "content": f"[系统提示：最近搜索到的课程：{cache_summary}。如需操作课程，可直接使用这些 ID。]"
            })

        # Call LLM with native tool_use support
        try:
            mimo = load_mimo()
            response_data = mimo.chat_completion_raw(messages, max_tokens=1024, temperature=0.3, tools=TOOLS)
            text, thinking, tool_use_blocks = _extract_all_blocks(response_data)
        except Exception as e:
            logger.warning("LLM call failed, using keyword fallback: %s", e)
            return _keyword_fallback(db, user, message, current_courses)

        # Try native tool_use blocks first, then fall back to JSON text parsing
        if tool_use_blocks:
            tool_calls = tool_use_blocks
            reply = text
        else:
            # Fallback: parse JSON from text (for models that don't support tool_use)
            raw_for_parse = text if text else thinking
            action = self._parse_json(raw_for_parse)
            if not action:
                logger.warning("LLM output not valid JSON, using keyword fallback. raw=%s", raw_for_parse[:200])
                return _keyword_fallback(db, user, message, current_courses)
            tool_calls = []
            if action.get("tool") and action["tool"] != "null":
                tool_calls = [{"type": "tool_use", "id": "text_call", "name": action["tool"], "input": action.get("tool_args", {})}]
            reply = action.get("reply", "")

        # If no tool call, check if the user has a clear intent that the LLM missed
        if not tool_calls:
            if not reply:
                return _keyword_fallback(db, user, message, current_courses)
            # Clean up reply if it's still JSON
            if reply.strip().startswith("{"):
                parsed = self._parse_json(reply)
                if parsed and parsed.get("reply"):
                    reply = parsed["reply"]
            # If LLM gave a reply but user has clear add/remove/list/recommend intent, force the action
            intent = _keyword_classify(message)
            if intent:
                if intent in ("list", "recommend"):
                    return _keyword_fallback(db, user, message, current_courses)
                codes = re.findall(r"[A-Za-z]{2,}\d{2,}", message)
                course_name = self._extract_course_name(message, intent)
                if intent in ("add", "remove") and (codes or course_name):
                    return _keyword_fallback(db, user, message, current_courses)
            self._log_history(db, user, message, "direct_reply")
            result = {"answer": reply}
            result["selected_courses"] = self._get_selected_courses(db, user.id)
            return result

        # Execute tool calls (multi-turn loop for native tool_use)
        last_tool_result = None
        last_tool_name = None

        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("input", {})
            tool_id = tc.get("id", "")

            # Resolve course IDs for course-related tools
            if tool_name in ("add_course", "remove_course", "replace_course"):
                self._resolve_course_ids(db, tool_args, message, user.id)

            # If still no course_id after resolution, fall back to keyword
            if tool_name in ("add_course", "remove_course") and not tool_args.get("course_id"):
                logger.warning("LLM called %s without course_id, falling back to keyword", tool_name)
                return _keyword_fallback(db, user, message, current_courses)

            tool_fn = TOOL_MAP.get(tool_name)
            if not tool_fn:
                logger.warning("Unknown tool: %s", tool_name)
                return _keyword_fallback(db, user, message, current_courses)

            try:
                tool_result = tool_fn(db, user.id, tool_args, current_courses)
            except Exception as e:
                logger.error("Tool %s failed: %s", tool_name, e)
                return _keyword_fallback(db, user, message, current_courses)

            # Cache search results for follow-up operations
            if tool_name == "search_courses" and tool_result.get("courses"):
                self._last_search[user.id] = tool_result["courses"]

            last_tool_result = tool_result
            last_tool_name = tool_name

            # If tool failed, return error via keyword fallback
            has_error = tool_result.get("error") or (tool_result.get("success") is False)
            if has_error:
                return _keyword_fallback(db, user, message, current_courses)

        # Build final response
        if not last_tool_result:
            return _keyword_fallback(db, user, message, current_courses)

        # For search/recommend, call LLM again for natural language presentation
        need_llm = last_tool_name in ("search_courses", "recommend_courses")

        if need_llm:
            final_reply = self._generate_natural_response(mimo, messages, last_tool_name, last_tool_result)
        else:
            final_reply = self._template_fallback(last_tool_name, last_tool_result)

        result = {"answer": final_reply}

        # Always sync selected courses from database
        result["selected_courses"] = self._get_selected_courses(db, user.id)

        # Include recommendations
        if last_tool_name == "recommend_courses" and last_tool_result.get("courses"):
            result["recommendations"] = last_tool_result["courses"]

        self._log_history(db, user, message, last_tool_name)
        return result

    def _get_selected_courses(self, db: Session, user_id: int):
        """Always fetch fresh selected courses from DB."""
        courses = (
            db.query(Course)
            .join(Selection, Selection.course_id == Course.id)
            .filter(Selection.user_id == user_id)
            .order_by(Course.faculty, Course.code)
            .all()
        )
        return courses or None

    def _resolve_course_ids(self, db: Session, tool_args: dict, message: str, user_id: int):
        """Normalize and resolve course IDs from string codes, message text, or cache."""
        for key in ("course_id", "old_course_id", "new_course_id"):
            cid = tool_args.get(key)
            if isinstance(cid, str):
                if cid.isdigit():
                    tool_args[key] = int(cid)
                else:
                    course = db.query(Course).filter(Course.code.ilike(cid)).first()
                    if course:
                        tool_args[key] = course.id

        # If course_id is missing entirely, try to resolve from message or cache
        if not tool_args.get("course_id"):
            codes = re.findall(r"[A-Za-z]{2,}\d{2,}", message)
            if codes:
                course = db.query(Course).filter(Course.code.ilike(codes[0])).first()
                if course:
                    tool_args["course_id"] = course.id
            if not tool_args.get("course_id") and user_id in self._last_search:
                cached = self._last_search[user_id]
                if len(cached) == 1:
                    tool_args["course_id"] = cached[0]["id"]

    def _generate_natural_response(self, mimo, messages, tool_name, tool_result):
        """Call LLM to generate a natural language response from tool results."""
        tool_context = json.dumps(tool_result, ensure_ascii=False, default=str)
        llm_messages = [
            {"role": "system", "content": f"你是小选，大学选课助手。用简洁友好的中文回复学生。不要输出JSON，直接用自然语言回复。"},
            {"role": "user", "content": f"工具 {tool_name} 的执行结果：\n{tool_context}\n\n请根据这个结果用自然语言回复学生。直接回复，不要输出JSON。"}
        ]
        try:
            text = mimo.chat_completion(llm_messages, max_tokens=1024, temperature=0.4)
            return text or self._template_fallback(tool_name, tool_result)
        except Exception as e:
            logger.error("LLM final response failed: %s", e)
            return self._template_fallback(tool_name, tool_result)

    def _build_system_prompt(self, user: User, current_courses: list[Course]) -> str:
        if current_courses:
            sel_lines = []
            for c in current_courses:
                sel_lines.append(f"- ID:{c.id} {c.code} {c.title}（{c.credits}学分，{c.instructor}，{c.schedule_display or '时间待定'}）")
            sel_text = "\n".join(sel_lines)
        else:
            sel_text = "（暂无选课）"

        return AGENT_SYSTEM_PROMPT.format(
            username=user.username,
            major=user.major or "未设置",
            grade=user.grade or "未设置",
            interests=user.interests or "未设置",
            current_selections=sel_text,
        )

    def _parse_json(self, raw: str) -> dict | None:
        text = raw.strip()

        # 1. Extract from markdown code block if present
        code_blocks = re.findall(r"```(?:json)?\s*\n?([\s\S]*?)```", text)
        for block in code_blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue

        # 2. Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 3. Find outermost complete JSON object using brace counting
        for i, ch in enumerate(text):
            if ch == "{":
                depth = 0
                for j in range(i, len(text)):
                    if text[j] == "{":
                        depth += 1
                    elif text[j] == "}":
                        depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[i:j + 1])
                        except json.JSONDecodeError:
                            break
        return None

    def _extract_course_name(self, message: str, intent: str) -> str:
        """Extract course name from Chinese message, e.g. '给我选有机化学' -> '有机化学'"""
        search_term = message
        if intent == "add":
            for kw in ["帮我选", "帮我加", "选课", "想上", "报名", "添加", "选", "加"]:
                search_term = search_term.replace(kw, "")
        elif intent == "remove":
            for kw in ["退掉", "退选", "取消", "删掉", "不要", "退", "删"]:
                search_term = search_term.replace(kw, "")
        return search_term.strip()

    def _template_fallback(self, tool_name: str, result: dict) -> str:
        if result.get("error"):
            return result["error"]

        if tool_name == "search_courses":
            courses = result.get("courses", [])
            if not courses:
                return "没有找到匹配的课程，试试换个关键词？"
            lines = [f"- {c['code']} {c['title']}（{c['credits']}学分，{c['instructor']}）" for c in courses[:8]]
            return f"找到 {len(courses)} 门课程：\n" + "\n".join(lines)

        if tool_name == "get_selections":
            courses = result.get("courses", [])
            if not courses:
                return "你目前还没有选修任何课程。"
            lines = [f"- {c['code']} {c['title']}（{c['credits']}学分）" for c in courses]
            return f"你当前已选 {len(courses)} 门课程，共 {result.get('total_credits', 0)} 学分：\n" + "\n".join(lines)

        if tool_name == "add_course":
            c = result.get("course", {})
            return f"已成功添加 {c.get('code', '')} {c.get('title', '')}。"

        if tool_name == "remove_course":
            c = result.get("course", {})
            return f"已退选 {c.get('code', '')} {c.get('title', '')}。"

        if tool_name == "replace_course":
            r = result.get("removed", {})
            a = result.get("added", {})
            return f"已将 {r.get('code', '')} 替换为 {a.get('code', '')}。"

        if tool_name == "recommend_courses":
            courses = result.get("courses", [])
            if not courses:
                return "暂时没有找到合适的推荐课程。"
            lines = [f"- {c['code']} {c['title']}（{c['credits']}学分，{c.get('faculty', '')}）" for c in courses]
            return "为你推荐以下课程：\n" + "\n".join(lines)

        return "操作完成。"

    def _log_history(self, db: Session, user: User, message: str, action: str):
        db.add(UserHistory(user_id=user.id, event_type="chat", payload={"message": message, "action": action}))
        db.commit()


agent = CourseAgent()
