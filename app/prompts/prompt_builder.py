"""prompt 组装器。

这个模块负责把历史消息和工具描述拼成一段完整 prompt，
供大模型做动作决策。
"""

from __future__ import annotations

from app.schemas.models import Message

ROLE_LABELS = {
    "system": "系统",
    "user": "用户",
    "assistant": "助手",
    "tool": "工具",
}


class PromptBuilder:
    """构造发送给模型的 prompt。"""

    def __init__(self, history_limit: int = 6) -> None:
        self.history_limit = history_limit

    def build(self, messages: list[Message], tool_description: str) -> str:
        """根据历史消息和工具说明生成 prompt 文本。"""

        history_lines = []
        # 这里只取最近几条历史，避免上下文无限增长。
        for message in messages[-self.history_limit :]:
            role_label = ROLE_LABELS.get(message.role, message.role)
            history_lines.append(f"{role_label}：{message.content}")

        history_text = "\n".join(history_lines) if history_lines else "（暂无历史对话）"

        return (
            "你是一个运行在本地命令行中的个人助手。\n"
            "你每一轮只能选择一个动作。\n"
            "你必须只输出合法 JSON，不能输出解释、前后缀、Markdown 代码块或额外文本。\n"
            '如果直接回答，使用 {"action": "respond", "answer": "..."}。\n'
            '如果需要调用工具，使用 {"action": "tool_call", "tool_name": "...", "arguments": {...}}。\n'
            "不要编造工具执行结果。\n"
            "当 action=respond 时，请使用用户当前使用的语言回答。\n\n"
            "可用工具如下：\n"
            f"{tool_description}\n\n"
            "最近对话如下：\n"
            f"{history_text}\n"
        )
