"""显式工具请求路由器。

这个模块只负责识别“用户已经明确点名要调用哪个工具”的场景，
用于在模型没有稳定遵守 JSON 协议时做兜底，不负责一般自然语言理解。
"""

from __future__ import annotations

import re

from app.schemas.models import ToolCall


class ToolRequestRouter:
    """把明确的工具请求直接解析成 ToolCall。"""

    _SAVE_MEMORY_KEY_PATTERN = re.compile(
        r"key\s*(?:设为|=|是)?\s*[\"'“”]?([A-Za-z0-9_-]+)[\"'“”]?",
        re.IGNORECASE,
    )
    _SAVE_MEMORY_VALUE_PATTERN = re.compile(
        r"value\s*(?:设为|=|是)?\s*[\"'“”]?(.+?)[\"'“”]?(?:[。！？!?,，；;]|$)",
        re.IGNORECASE,
    )
    _GET_MEMORY_KEY_PATTERN = re.compile(
        r"(?:key\s*(?:设为|=|是)?|查询|读取)\s*[\"'“”]?([A-Za-z0-9_-]+)[\"'“”]?(?:[。！？!?,，；;]|$)",
        re.IGNORECASE,
    )
    _ADD_TODO_TASK_PATTERN = re.compile(
        r"(?:记录待办|添加待办|待办|task)\s*[:：]\s*(.+?)(?:[。！？!?；;]|$)",
        re.IGNORECASE,
    )

    def route(self, user_input: str) -> ToolCall | None:
        """把用户输入中的显式工具请求解析成 ToolCall。"""

        normalized_text = " ".join(user_input.strip().split())
        lowered_text = normalized_text.lower()

        if "save_memory" in lowered_text:
            key = self._extract_first_group(self._SAVE_MEMORY_KEY_PATTERN, normalized_text)
            value = self._extract_first_group(self._SAVE_MEMORY_VALUE_PATTERN, normalized_text)
            if key and value:
                return ToolCall(tool_name="save_memory", arguments={"key": key, "value": value})

        if "get_memory" in lowered_text:
            key = self._extract_first_group(self._GET_MEMORY_KEY_PATTERN, normalized_text)
            if key:
                return ToolCall(tool_name="get_memory", arguments={"key": key})

        if "add_todo" in lowered_text:
            task = self._extract_first_group(self._ADD_TODO_TASK_PATTERN, normalized_text)
            if task:
                return ToolCall(tool_name="add_todo", arguments={"task": task})

        if "list_todos" in lowered_text:
            return ToolCall(tool_name="list_todos", arguments={})

        return None

    def _extract_first_group(self, pattern: re.Pattern[str], text: str) -> str | None:
        """提取正则的第一个分组并做最小清洗。"""

        match = pattern.search(text)
        if match is None:
            return None

        cleaned_text = match.group(1).strip().strip("\"'“”")
        cleaned_text = cleaned_text.removesuffix("不要直接回答").strip()
        cleaned_text = cleaned_text.removesuffix("必须调用工具").strip()
        return cleaned_text or None
