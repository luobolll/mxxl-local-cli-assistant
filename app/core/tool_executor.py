"""执行模型选择的工具。"""

from __future__ import annotations

from app.core.tool_registry import ToolRegistry
from app.schemas.models import ToolCall, ToolResult


class ToolExecutor:
    """根据 ToolCall 找到对应工具并执行。"""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行一次工具调用，并统一封装成功或失败结果。"""

        tool_definition = self.tool_registry.get(tool_call.tool_name)
        try:
            # 这里用 **arguments 把字典参数展开成关键字参数，方便直接调用 Python 函数。
            result = tool_definition.handler(**tool_call.arguments)
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=True,
                data=result,
            )
        except TypeError as exc:
            # TypeError 通常意味着函数参数名不匹配，单独提示更容易定位问题。
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                data={},
                error=f"工具参数不合法：{exc}",
            )
        except Exception as exc:
            # 其他异常统一归为工具执行失败。
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                data={},
                error=f"工具执行失败：{exc}",
            )
