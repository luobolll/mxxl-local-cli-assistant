"""工具注册表。

这个模块负责记录系统里可调用的工具有哪些，以及每个工具对应的说明和处理函数。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolDefinition:
    """描述一个工具的静态信息。"""

    name: str
    description: str
    input_schema: dict[str, str]
    handler: Callable[..., dict[str, Any]]


class ToolRegistry:
    """保存并查询已注册工具。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool_definition: ToolDefinition) -> None:
        """注册一个新工具。"""

        if tool_definition.name in self._tools:
            raise ValueError(f"工具已注册：{tool_definition.name}")
        self._tools[tool_definition.name] = tool_definition

    def get(self, tool_name: str) -> ToolDefinition:
        """按工具名获取工具定义。"""

        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise ValueError(f"未知工具：{tool_name}") from exc

    def list_definitions(self) -> list[ToolDefinition]:
        """返回所有已注册工具定义。"""

        return list(self._tools.values())

    def render_prompt_description(self) -> str:
        """把工具信息渲染成 prompt 可直接使用的文本。"""

        lines: list[str] = []
        for tool in self.list_definitions():
            lines.append(f"工具名：{tool.name}")
            lines.append(f"用途：{tool.description}")
            if tool.input_schema:
                lines.append(f"参数：{tool.input_schema}")
            else:
                lines.append("参数：{}")
            lines.append("")
        return "\n".join(lines).strip()
