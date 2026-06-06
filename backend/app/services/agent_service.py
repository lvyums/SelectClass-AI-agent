"""
智能选课助手服务 — CourseAgent

使用 MiMo LLM 实现智能对话式选课。
支持工具调用（搜索、选课、退课、换课、推荐），
当 LLM 不可用时自动降级为关键词匹配。
"""

import json
import logging
import re

from ..extensions import db
from ..models.course import Course
from ..models.selection import Selection
from ..models.user import User
from ..models.history import UserHistory
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
        "description": "按关键词搜索课程。支持课程名、课程代号、教师名、院系名搜索。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"}
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
        "description": "将一门课程加入学生的选课列表。需要先通过 search_courses 获取课程 ID。",
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {"type": "integer", "description": "课程的数字 ID"}
            },
            "required": ["course_id"]
        }
    },
    {
        "name": "remove_course",
        "description": "从学生选课列表中移除一门课程。",
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
        "description": "将一门已选课程替换为另一门新课程。",
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
        "description": "根据学生的专业、年级和兴趣推荐课程。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "推荐方向关键词"}
            }
        }
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

def _exec_search_courses(keyword: str) -> dict:
    from sqlalchemy import or_
    kw = keyword.strip()
    if not kw:
        return {"courses": [], "message": "请输入搜索关键词"}

    conditions = [
        Course.title.contains(kw),
        Course.code.contains(kw.upper()),
        Course.instructor.contains(kw),
        Course.faculty.contains(kw),
    ]
    if Course.keywords is not None:
        conditions.append(Course.keywords.contains(kw))
    courses = db.session.query(Course).filter(or_(*conditions)).limit(15).all()

    if not courses:
        for suffix in ["课程", "课", "专业", "学院"]:
            if kw.endswith(suffix) and len(kw) > len(suffix):
                shorter = kw[:-len(suffix)]
                conditions = [Course.title.contains(shorter), Course.faculty.contains(shorter)]
                if Course.keywords is not None:
                    conditions.append(Course.keywords.contains(shorter))
                courses = db.session.query(Course).filter(or_(*conditions)).limit(15).all()
                if courses:
                    break

    return {
        "courses": [
            {
                "id": c.id, "code": c.code, "title": c.title,
                "credits": c.credits, "instructor": c.instructor,
                "faculty": c.faculty, "level": c.level,
                "course_type": c.course_type, "schedule": c.schedule_display or "",
                "difficulty": c.difficulty, "summary": (c.summary or "")[:100],
            }
            for c in courses
        ],
        "count": len(courses),
    }


def _exec_get_selections(user_id: int) -> dict:
    courses = (
        db.session.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == user_id)
        .order_by(Course.faculty, Course.code)
        .all()
    )
    total_credits = sum(c.credits for c in courses)
    return {
        "courses": [
            {"id": c.id, "code": c.code, "title": c.title, "credits": c.credits,
             "instructor": c.instructor, "schedule": c.schedule_display or ""}
            for c in courses
        ],
        "count": len(courses),
        "total_credits": total_credits,
    }


def _exec_add_course(user_id: int, course_id: int, current_courses: list) -> dict:
    course = db.session.query(Course).filter(Course.id == course_id).first()
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

    db.session.add(Selection(user_id=user_id, course_id=course_id))
    db.session.commit()
    return {"success": True, "course": {"id": course.id, "code": course.code, "title": course.title, "credits": course.credits}}


def _exec_remove_course(user_id: int, course_id: int) -> dict:
    course = db.session.query(Course).filter(Course.id == course_id).first()
    if not course:
        return {"success": False, "error": f"未找到 ID 为 {course_id} 的课程"}

    sel = db.session.query(Selection).filter(Selection.user_id == user_id, Selection.course_id == course_id).first()
    if not sel:
        return {"success": False, "error": f"你没有选 {course.code} {course.title}，无法退选"}

    db.session.delete(sel)
    db.session.commit()
    return {"success": True, "course": {"code": course.code, "title": course.title}}


def _exec_replace_course(user_id: int, old_id: int, new_id: int, current_courses: list) -> dict:
    old_course = db.session.query(Course).filter(Course.id == old_id).first()
    new_course = db.session.query(Course).filter(Course.id == new_id).first()
    if not old_course:
        return {"success": False, "error": f"未找到 ID 为 {old_id} 的课程"}
    if not new_course:
        return {"success": False, "error": f"未找到 ID 为 {new_id} 的课程"}

    sel = db.session.query(Selection).filter(Selection.user_id == user_id, Selection.course_id == old_id).first()
    if not sel:
        return {"success": False, "error": f"你没有选 {old_course.code} {old_course.title}，无法替换"}

    remaining = [c for c in current_courses if c.id != old_id]
    conflict = find_conflict(remaining, [new_course])
    if conflict:
        return {"success": False, "error": f"{new_course.code} 与已选的 {conflict.code} 时间冲突，无法替换"}

    try:
        db.session.delete(sel)
        db.session.add(Selection(user_id=user_id, course_id=new_id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {
        "success": True,
        "removed": {"code": old_course.code, "title": old_course.title},
        "added": {"code": new_course.code, "title": new_course.title},
    }


def _exec_recommend_courses(user: User, query: str) -> dict:
    from .recommendation_service import recommend_courses
    recs = recommend_courses(user, query, limit=8)
    return {
        "courses": [
            {
                "id": c.id, "code": c.code, "title": c.title,
                "credits": c.credits, "instructor": c.instructor,
                "faculty": c.faculty, "level": c.level,
                "course_type": c.course_type, "difficulty": c.difficulty,
                "summary": (c.summary or "")[:80],
            }
            for c in recs
        ],
        "count": len(recs),
    }


TOOL_MAP = {
    "search_courses": lambda uid, args, cc: _exec_search_courses(args.get("keyword", "")),
    "get_selections": lambda uid, args, cc: _exec_get_selections(uid),
    "add_course": lambda uid, args, cc: _exec_add_course(uid, args.get("course_id"), cc),
    "remove_course": lambda uid, args, cc: _exec_remove_course(uid, args.get("course_id")),
    "replace_course": lambda uid, args, cc: _exec_replace_course(uid, args.get("old_course_id"), args.get("new_course_id"), cc),
    "recommend_courses": lambda uid, args, cc: _exec_recommend_courses(_get_user(uid), args.get("query", "")),
}


def _get_user(user_id: int) -> User:
    return db.session.query(User).filter(User.id == user_id).first()


def _sanitize_for_prompt(value: str, max_len: int = 100) -> str:
    """清理用户输入，防止 prompt 注入"""
    if not value:
        return ""
    cleaned = value.replace("{", "").replace("}", "").replace("\\", "")
    cleaned = cleaned.replace("\n", " ").replace("\r", "")
    return cleaned[:max_len].strip()

# ---------------------------------------------------------------------------
# Keyword fallback
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


def _keyword_fallback(user: User, message: str, current_courses: list) -> dict:
    from sqlalchemy import or_
    intent = _keyword_classify(message)
    codes = re.findall(r"[A-Za-z]{2,}\d{2,}", message)

    if intent == "list":
        if not current_courses:
            return {"answer": "你目前还没有选修任何课程。"}
        lines = [f"- {c.code} {c.title}（{c.credits}学分）" for c in current_courses]
        total = sum(c.credits for c in current_courses)
        return {"answer": f"你当前已选 {len(current_courses)} 门课程，共 {total} 学分：\n" + "\n".join(lines)}

    if intent == "recommend":
        result = _exec_recommend_courses(user, message)
        if result["courses"]:
            lines = [f"- {c['code']} {c['title']}（{c['credits']}学分）" for c in result["courses"]]
            return {"answer": "为你推荐以下课程：\n" + "\n".join(lines), "recommendations": result["courses"]}
        return {"answer": "暂时没有找到合适的推荐课程。"}

    if intent == "add":
        results = []
        changed = False
        for code in codes:
            course = db.session.query(Course).filter(Course.code.ilike(code)).first()
            if course:
                r = _exec_add_course(user.id, course.id, current_courses)
                if r["success"]:
                    current_courses.append(course)
                    changed = True
                    results.append(f"已添加 {course.code} {course.title}")
                else:
                    results.append(r["error"])
            else:
                results.append(f"未找到课程 {code}")

        if not codes:
            search_term = message
            for kw in ["帮我选", "帮我加", "选课", "选", "加", "想上", "报名", "添加"]:
                search_term = search_term.replace(kw, "")
            search_term = search_term.strip()
            if search_term:
                matched = db.session.query(Course).filter(
                    or_(Course.title.contains(search_term), Course.faculty.contains(search_term))
                ).limit(5).all()
                if len(matched) == 1:
                    r = _exec_add_course(user.id, matched[0].id, current_courses)
                    if r["success"]:
                        current_courses.append(matched[0])
                        changed = True
                        results.append(f"已添加 {matched[0].code} {matched[0].title}")
                    else:
                        results.append(r["error"])
                elif len(matched) > 1:
                    lines = [f"- {c.code} {c.title}（{c.credits}学分，{c.instructor}）" for c in matched]
                    return {"answer": "找到多门相关课程，请指定：\n" + "\n".join(lines)}
                else:
                    results.append(f"未找到与「{search_term}」相关的课程")

        resp = {"answer": "。".join(results) + "。"}
        if changed:
            resp["selected_courses"] = (
                db.session.query(Course)
                .join(Selection, Selection.course_id == Course.id)
                .filter(Selection.user_id == user.id)
                .order_by(Course.faculty, Course.code).all()
            )
        return resp

    if intent == "remove":
        results = []
        changed = False
        for code in codes:
            course = db.session.query(Course).filter(Course.code.ilike(code)).first()
            if course:
                r = _exec_remove_course(user.id, course.id)
                if r["success"]:
                    changed = True
                    results.append(f"已退选 {code}")
                else:
                    results.append(r["error"])
            else:
                results.append(f"未找到课程 {code}")

        if not codes:
            search_term = message
            for kw in ["退掉", "退选", "取消", "删掉", "不要", "退", "删"]:
                search_term = search_term.replace(kw, "")
            search_term = search_term.strip()
            if search_term:
                matched = [c for c in current_courses if search_term in (c.title or "") or search_term in (c.keywords or "")]
                if len(matched) == 1:
                    r = _exec_remove_course(user.id, matched[0].id)
                    if r["success"]:
                        changed = True
                        results.append(f"已退选 {matched[0].code} {matched[0].title}")
                    else:
                        results.append(r["error"])
                elif len(matched) > 1:
                    lines = [f"- {c.code} {c.title}" for c in matched]
                    return {"answer": "你选了多门相关课程，请指定退哪门：\n" + "\n".join(lines)}
                else:
                    results.append(f"你在已选课程中没有找到「{search_term}」")

        resp = {"answer": "。".join(results) + "。"}
        if changed:
            resp["selected_courses"] = (
                db.session.query(Course)
                .join(Selection, Selection.course_id == Course.id)
                .filter(Selection.user_id == user.id)
                .order_by(Course.faculty, Course.code).all()
            )
        return resp

    return {"answer": "抱歉，我暂时无法理解你的请求。你可以试试：\n- 帮我选 CS101\n- 退掉数学课\n- 我选了哪些课\n- 推荐一些课"}

# ---------------------------------------------------------------------------
# Main Agent
# ---------------------------------------------------------------------------

MAX_CACHED_USERS = 500


class CourseAgent:
    """智能选课助手 — 封装 LLM 对话和工具调用逻辑"""

    def __init__(self):
        self._last_search: dict[int, list[dict]] = {}

    def _evict_cache(self):
        """当缓存用户数超过上限时，清理最早的条目"""
        if len(self._last_search) > MAX_CACHED_USERS:
            keys = list(self._last_search.keys())
            for k in keys[: len(keys) // 4]:
                self._last_search.pop(k, None)

    def handle_message(self, user: User, message: str, history: list[dict]) -> dict:
        """处理用户消息，返回 {answer, selected_courses?, recommendations?}"""
        self._evict_cache()
        message = _sanitize_for_prompt(message, 1000)
        current_courses = (
            db.session.query(Course)
            .join(Selection, Selection.course_id == Course.id)
            .filter(Selection.user_id == user.id)
            .all()
        )

        # 缓存确认：用户回复"好的"等确认词时直接添加缓存的课程
        if message.strip() in CONFIRM_WORDS and user.id in self._last_search:
            cached = self._last_search[user.id]
            if len(cached) == 1:
                r = _exec_add_course(user.id, cached[0]["id"], current_courses)
                self._last_search.pop(user.id, None)
                updated = _get_selected_courses(user.id)
                if r.get("success"):
                    return {"answer": f"已成功添加 {r['course']['code']} {r['course']['title']}。", "selected_courses": updated}
                return {"answer": r.get("error", "添加失败"), "selected_courses": updated}
            elif len(cached) > 1:
                lines = [f"- {c['code']} {c['title']}（{c['credits']}学分）" for c in cached]
                return {"answer": "请指定你要选哪门课（输入课程代号）：\n" + "\n".join(lines)}

        # 构建 LLM 消息
        system_prompt = self._build_system_prompt(user, current_courses)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        if user.id in self._last_search and self._last_search[user.id]:
            cached = self._last_search[user.id]
            cache_summary = ", ".join(f"{c['code']}(ID:{c['id']})" for c in cached[:5])
            messages.append({"role": "user", "content": f"[系统提示：最近搜索到的课程：{cache_summary}。如需操作课程，可直接使用这些 ID。]"})

        # 调用 LLM
        try:
            mimo = load_mimo()
            response_data = mimo.chat_completion_raw(messages, max_tokens=1024, temperature=0.3, tools=TOOLS)
            text, thinking, tool_use_blocks = _extract_all_blocks(response_data)
        except Exception as e:
            logger.warning("LLM call failed, using keyword fallback: %s", e)
            return _keyword_fallback(user, message, current_courses)

        # 解析工具调用
        if tool_use_blocks:
            tool_calls = tool_use_blocks
            reply = text
        else:
            raw_for_parse = text if text else thinking
            action = self._parse_json(raw_for_parse)
            if not action:
                return _keyword_fallback(user, message, current_courses)
            tool_calls = []
            if action.get("tool") and action["tool"] != "null":
                tool_calls = [{"type": "tool_use", "id": "text_call", "name": action["tool"], "input": action.get("tool_args", {})}]
            reply = action.get("reply", "")

        if not tool_calls:
            if not reply:
                return _keyword_fallback(user, message, current_courses)
            if reply.strip().startswith("{"):
                parsed = self._parse_json(reply)
                if parsed and parsed.get("reply"):
                    reply = parsed["reply"]
            intent = _keyword_classify(message)
            if intent:
                if intent in ("list", "recommend"):
                    return _keyword_fallback(user, message, current_courses)
                codes = re.findall(r"[A-Za-z]{2,}\d{2,}", message)
                if intent in ("add", "remove") and codes:
                    return _keyword_fallback(user, message, current_courses)
            self._log_history(user, message, "direct_reply")
            return {"answer": reply, "selected_courses": _get_selected_courses(user.id)}

        # 执行工具调用
        last_tool_result = None
        last_tool_name = None

        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc.get("input", {})

            if tool_name in ("add_course", "remove_course", "replace_course"):
                self._resolve_course_ids(tool_args, message, user.id)

            if tool_name in ("add_course", "remove_course") and not tool_args.get("course_id"):
                return _keyword_fallback(user, message, current_courses)

            tool_fn = TOOL_MAP.get(tool_name)
            if not tool_fn:
                return _keyword_fallback(user, message, current_courses)

            try:
                tool_result = tool_fn(user.id, tool_args, current_courses)
            except Exception as e:
                logger.error("Tool %s failed: %s", tool_name, e)
                db.session.rollback()
                return _keyword_fallback(user, message, current_courses)

            if tool_name == "search_courses" and tool_result.get("courses"):
                self._last_search[user.id] = tool_result["courses"]

            last_tool_result = tool_result
            last_tool_name = tool_name

            if tool_result.get("error") or (tool_result.get("success") is False):
                return _keyword_fallback(user, message, current_courses)

        if not last_tool_result:
            return _keyword_fallback(user, message, current_courses)

        # 对搜索/推荐结果生成自然语言回复
        if last_tool_name in ("search_courses", "recommend_courses"):
            final_reply = self._generate_natural_response(mimo, messages, last_tool_name, last_tool_result)
        else:
            final_reply = self._template_fallback(last_tool_name, last_tool_result)

        result = {"answer": final_reply, "selected_courses": _get_selected_courses(user.id)}
        if last_tool_name == "recommend_courses" and last_tool_result.get("courses"):
            result["recommendations"] = last_tool_result["courses"]

        self._log_history(user, message, last_tool_name)
        return result

    def _resolve_course_ids(self, tool_args: dict, message: str, user_id: int):
        for key in ("course_id", "old_course_id", "new_course_id"):
            cid = tool_args.get(key)
            if isinstance(cid, str):
                if cid.isdigit():
                    tool_args[key] = int(cid)
                else:
                    course = db.session.query(Course).filter(Course.code.ilike(cid)).first()
                    if course:
                        tool_args[key] = course.id

        if not tool_args.get("course_id"):
            codes = re.findall(r"[A-Za-z]{2,}\d{2,}", message)
            if codes:
                course = db.session.query(Course).filter(Course.code.ilike(codes[0])).first()
                if course:
                    tool_args["course_id"] = course.id
            if not tool_args.get("course_id") and user_id in self._last_search:
                cached = self._last_search[user_id]
                if len(cached) == 1:
                    tool_args["course_id"] = cached[0]["id"]

    def _generate_natural_response(self, mimo, messages, tool_name, tool_result):
        tool_context = json.dumps(tool_result, ensure_ascii=False, default=str)
        llm_messages = [
            {"role": "system", "content": "你是小选，大学选课助手。用简洁友好的中文回复学生。不要输出JSON，直接用自然语言回复。"},
            {"role": "user", "content": f"工具 {tool_name} 的执行结果：\n{tool_context}\n\n请根据这个结果用自然语言回复学生。"}
        ]
        try:
            text = mimo.chat_completion(llm_messages, max_tokens=1024, temperature=0.4)
            return text or self._template_fallback(tool_name, tool_result)
        except Exception:
            return self._template_fallback(tool_name, tool_result)

    def _build_system_prompt(self, user: User, current_courses: list) -> str:
        if current_courses:
            sel_lines = [f"- ID:{c.id} {c.code} {c.title}（{c.credits}学分，{c.instructor}，{c.schedule_display or '时间待定'}）" for c in current_courses]
            sel_text = "\n".join(sel_lines)
        else:
            sel_text = "（暂无选课）"
        return AGENT_SYSTEM_PROMPT.format(
            username=_sanitize_for_prompt(user.username, 50),
            major=_sanitize_for_prompt(user.major, 50) or "未设置",
            grade=_sanitize_for_prompt(user.grade, 20) or "未设置",
            interests=_sanitize_for_prompt(user.interests, 100) or "未设置",
            current_selections=sel_text,
        )

    def _parse_json(self, raw: str) -> dict | None:
        text = raw.strip()
        code_blocks = re.findall(r"```(?:json)?\s*\n?([\s\S]*?)```", text)
        for block in code_blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
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

    def _log_history(self, user: User, message: str, action: str):
        db.session.add(UserHistory(user_id=user.id, event_type="chat", payload={"message": message, "action": action}))
        db.session.commit()


def _get_selected_courses(user_id: int):
    courses = (
        db.session.query(Course)
        .join(Selection, Selection.course_id == Course.id)
        .filter(Selection.user_id == user_id)
        .order_by(Course.faculty, Course.code).all()
    )
    return courses or None


# 全局单例 — Singleton Pattern
agent = CourseAgent()
