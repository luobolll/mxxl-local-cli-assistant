"""把系统内部结果转换成用户可读文本。"""

from __future__ import annotations

import json
from typing import Any

from app.schemas.models import ToolResult


class ResponseFormatter:
    """统一负责最终文本格式化。

    这样可以避免把回复文案散落在 Orchestrator 和各个工具里。
    """

    def format_direct_answer(self, answer: str) -> str:
        """格式化模型直接给出的自然语言回答。"""

        return answer.strip()

    def format_tool_result(self, tool_result: ToolResult) -> str:
        """根据不同工具的返回结果，生成统一的用户回复文本。"""

        if not tool_result.success:
            return self.format_error(tool_result.error or "工具执行失败。")

        if tool_result.tool_name == "add_todo":
            return f"已记录待办：{tool_result.data['task']}"

        if tool_result.tool_name == "list_todos":
            items = tool_result.data.get("items", [])
            if not items:
                return "当前没有未完成的待办。"
            lines = ["当前待办："]
            for item in items:
                lines.append(f"- [{item['id']}] {item['task']}")
            return "\n".join(lines)

        if tool_result.tool_name == "save_memory":
            return f"已记住：{tool_result.data['key']} = {tool_result.data['value']}"

        if tool_result.tool_name == "get_memory":
            value = tool_result.data.get("value")
            if value is None:
                return f"没有找到键为 {tool_result.data['key']} 的记忆"
            return f"已找到记忆：{tool_result.data['key']} = {value}"

        return "工具执行完成。"

    def format_error(self, error_message: str) -> str:
        """统一错误输出格式。"""

        return error_message

    def to_json_text(self, payload: dict[str, Any]) -> str:
        """把字典稳定地转换成 JSON 文本，便于写入 trace。"""

        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
