"""共享数据模型定义。

当前项目用 Pydantic 来做结构校验，
这样模型输出、工具调用结果和 trace 记录都能保持统一格式。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


def utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 字符串。"""

    return datetime.now(timezone.utc).isoformat()


class Message(BaseModel):
    """一条消息记录。"""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    created_at: str = Field(default_factory=utc_now_iso)


class ToolCall(BaseModel):
    """一次工具调用请求。"""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """一次工具执行结果。"""

    tool_name: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ActionDecision(BaseModel):
    """模型输出的动作决策。

    这个对象表示模型本轮到底是直接回答，还是请求调用工具。
    """

    action: Literal["respond", "tool_call"]
    answer: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_action_shape(self) -> "ActionDecision":
        """根据 action 的不同，检查必须字段是否存在。"""

        if self.action == "respond" and not self.answer:
            raise ValueError("当 action=respond 时，必须提供 answer 字段。")
        if self.action == "tool_call":
            if not self.tool_name:
                raise ValueError("当 action=tool_call 时，必须提供 tool_name 字段。")
            if not isinstance(self.arguments, dict):
                raise ValueError("arguments 必须是 JSON 对象。")
        return self


class TraceRecord(BaseModel):
    """保存一次完整请求处理过程中的关键数据。"""

    session_id: str
    user_input: str
    prompt_text: str
    model_output: str
    action_type: str
    tool_name: str | None = None
    tool_args_json: str | None = None
    tool_result_json: str | None = None
    final_response: str
    created_at: str = Field(default_factory=utc_now_iso)
