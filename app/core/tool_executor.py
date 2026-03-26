"""执行模型选择的工具。"""

from __future__ import annotations

from typing import Any

from app.core.errors import ToolArgumentError, ToolExecutionError, ToolNotFoundError
from app.core.tool_registry import ToolRegistry
from app.schemas.models import ToolCall, ToolResult


class ToolExecutor:
    """根据 ToolCall 找到对应工具并执行。"""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行一次工具调用，并统一封装成功或失败结果。"""

        try:
            tool_definition = self.tool_registry.get(tool_call.tool_name)
        except ValueError as exc:
            raise ToolNotFoundError(f"未知工具：{tool_call.tool_name}") from exc

        self._validate_arguments(
            tool_name=tool_call.tool_name,
            input_schema=tool_definition.input_schema,
            arguments=tool_call.arguments,
        )

        try:
            # 这里用 **arguments 把字典参数展开成关键字参数，方便直接调用 Python 函数。
            result = tool_definition.handler(**tool_call.arguments)
            return ToolResult(
                tool_name=tool_call.tool_name,
                success=True,
                data=result,
            )
        except TypeError as exc:
            raise ToolArgumentError(f"工具 {tool_call.tool_name} 参数不匹配：{exc}") from exc
        except Exception as exc:
            raise ToolExecutionError(f"工具 {tool_call.tool_name} 执行异常：{exc}") from exc

    def _validate_arguments(
        self,
        tool_name: str,
        input_schema: dict[str, str],
        arguments: dict[str, Any],
    ) -> None:
        """按注册表声明校验工具参数。

        当前架构里四个工具都只接受字符串参数或空参数，
        所以这里先做最小、稳定、容易理解的校验。
        """

        expected_keys = set(input_schema.keys())
        actual_keys = set(arguments.keys())

        missing_keys = expected_keys - actual_keys
        if missing_keys:
            missing_text = ", ".join(sorted(missing_keys))
            raise ToolArgumentError(f"工具 {tool_name} 缺少参数：{missing_text}")

        unexpected_keys = actual_keys - expected_keys
        if unexpected_keys:
            unexpected_text = ", ".join(sorted(unexpected_keys))
            raise ToolArgumentError(f"工具 {tool_name} 出现未声明参数：{unexpected_text}")

        for key, value_type in input_schema.items():
            if value_type == "字符串" and not isinstance(arguments[key], str):
                raise ToolArgumentError(f"工具 {tool_name} 的参数 {key} 必须是字符串")
