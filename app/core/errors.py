"""系统内部错误类型。

这个模块负责把内部异常映射成稳定的用户提示语，
避免把底层实现细节直接暴露给命令行用户。
"""

from __future__ import annotations


class AssistantError(Exception):
    """系统内可预期的业务异常。

    user_message 是最终展示给用户的固定文案，
    detail_message 用于在日志里保留更具体的排查信息。
    """

    def __init__(self, user_message: str, detail_message: str | None = None) -> None:
        super().__init__(detail_message or user_message)
        self.user_message = user_message
        self.detail_message = detail_message or user_message


class ModelOutputParseError(AssistantError):
    """模型输出不是合法 JSON。"""

    def __init__(self, detail_message: str) -> None:
        super().__init__("模型输出解析失败，请重试", detail_message)


class ModelOutputSchemaError(AssistantError):
    """模型输出字段不完整或不符合动作协议。"""

    def __init__(self, detail_message: str) -> None:
        super().__init__("模型输出字段不完整，请重试", detail_message)


class ToolNotFoundError(AssistantError):
    """模型请求了不存在的工具。"""

    def __init__(self, detail_message: str) -> None:
        super().__init__("请求的工具不存在", detail_message)


class ToolArgumentError(AssistantError):
    """工具参数缺失、类型不符或存在多余字段。"""

    def __init__(self, detail_message: str) -> None:
        super().__init__("工具参数不合法", detail_message)


class ToolExecutionError(AssistantError):
    """工具执行过程中发生了异常。"""

    def __init__(self, detail_message: str) -> None:
        super().__init__("工具执行失败", detail_message)
