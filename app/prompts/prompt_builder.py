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

    def build_user_prompt(self, messages: list[Message]) -> str:
        """根据历史消息生成 user 侧上下文。"""

        history_lines = []
        # 这里只取最近几条历史，避免上下文无限增长。
        for message in messages[-self.history_limit :]:
            role_label = ROLE_LABELS.get(message.role, message.role)
            history_lines.append(f"{role_label}：{message.content}")

        history_text = "\n".join(history_lines) if history_lines else "（暂无历史对话）"
        return (
            "最近对话如下：\n"
            f"{history_text}\n\n"
            "请严格按照系统要求，只返回一个 JSON 对象，不要返回任何解释文本。"
        )

    def build_system_prompt(self, tool_description: str) -> str:
        """构造 system 侧规则提示词。"""

        return (
            "你是一个运行在本地命令行中的个人助手。\n"
            "你只能输出合法 JSON，不能输出解释、前后缀、Markdown 代码块或额外文本。\n"
            "你每一轮只能选择一个动作：直接回答或调用一个工具。\n"
            "action 只能是 respond 或 tool_call。\n"
            "如果你决定调用工具，action 仍然必须写 tool_call，绝对不能把 action 写成 add_todo、list_todos、save_memory、get_memory。\n"
            "tool_name 字段才是工具名字段，不能省略，不能放错位置。\n"
            "如果用户明确要求调用某个工具，就必须返回 tool_call，不要改成自然语言回答。\n"
            "如果用户要求保存或查询待办、记忆，优先调用工具，不要编造已经执行过的结果。\n"
            "如果用户要求调用工具，而你输出 respond 或输出自然语言句子，这是错误的。\n"
            '如果直接回答，使用 {"action": "respond", "answer": "..."}。\n'
            '如果需要调用工具，使用 {"action": "tool_call", "tool_name": "...", "arguments": {...}}。\n'
            "不要编造工具执行结果。\n"
            "如果用户要记录信息，优先调用 save_memory。\n"
            "如果用户要查看记忆，调用 get_memory。\n"
            "如果用户要记录待办，调用 add_todo。\n"
            "如果用户要查看待办，调用 list_todos。\n"
            "当 action=tool_call 时，tool_name 必须是已注册工具名，arguments 必须是 JSON object。\n"
            "当 action=respond 时，请使用用户当前使用的语言回答。\n\n"
            "可用工具如下：\n"
            f"{tool_description}\n\n"
            "下面是合法输出示例：\n"
            '{"action": "respond", "answer": "你好"}\n'
            '{"action": "tool_call", "tool_name": "save_memory", "arguments": {"key": "favorite_drink", "value": "coffee"}}\n'
            '{"action": "tool_call", "tool_name": "add_todo", "arguments": {"task": "参加明天早上8:00的会议"}}\n\n'
            "下面是错误输出示例，绝对不要这样输出：\n"
            '{"action": "add_todo", "arguments": {"task": "参加明天早上8:00的会议"}}\n'
            '{"action": "save_memory", "arguments": {"key": "favorite_drink", "value": "coffee"}}\n'
            'Todo added successfully.\n\n'
            "输出前请做最后一次自检：\n"
            "1. 整个回答是否只有一个 JSON 对象。\n"
            "2. action 是否只可能是 respond 或 tool_call。\n"
            "3. 如果 action=tool_call，tool_name 和 arguments 是否齐全。"
        )

    def build(self, messages: list[Message], tool_description: str) -> str:
        """根据历史消息和工具说明生成可写入 trace 的完整 prompt 文本。"""

        system_prompt = self.build_system_prompt(tool_description)
        user_prompt = self.build_user_prompt(messages)
        return f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}"
