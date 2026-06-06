"""参数校验工具"""


def validate_required(data: dict, fields: list[str]) -> str | None:
    """校验必填字段，返回第一个缺失字段的错误信息，或 None"""
    for field in fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return f"字段 '{field}' 不能为空"
    return None


def validate_length(value: str, field_name: str, min_len: int = 0, max_len: int = 9999) -> str | None:
    """校验字符串长度"""
    if len(value) < min_len:
        return f"'{field_name}' 长度不能少于 {min_len} 个字符"
    if len(value) > max_len:
        return f"'{field_name}' 长度不能超过 {max_len} 个字符"
    return None
