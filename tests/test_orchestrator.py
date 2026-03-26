"""Orchestrator 关键链路测试。

这里用假依赖隔离网络和数据库，专门验证编排层是否遵守架构文档规定的
固定文案、单轮单动作和异常处理行为。
"""

from __future__ import annotations

import unittest

from app.core.orchestrator import Orchestrator
from app.core.response_formatter import ResponseFormatter
from app.core.session_manager import SessionManager
from app.core.tool_executor import ToolExecutor
from app.core.tool_registry import ToolDefinition, ToolRegistry
from app.parsers.decision_parser import DecisionParser
from app.prompts.prompt_builder import PromptBuilder
from app.schemas.models import Message, TraceRecord


class FakeLLMClient:
    """返回预设模型输出的假客户端。"""

    def __init__(self, raw_output: str) -> None:
        self.raw_output = raw_output
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.raw_output


class InMemoryMessageStore:
    """只在内存中保存消息，避免测试依赖 SQLite。"""

    def __init__(self) -> None:
        self.records: list[tuple[str, Message]] = []

    def add_message(self, session_id: str, role: str, content: str) -> Message:
        message = Message(role=role, content=content)
        self.records.append((session_id, message))
        return message

    def list_recent_messages(self, session_id: str, limit: int) -> list[Message]:
        messages = [message for record_session_id, message in self.records if record_session_id == session_id]
        return messages[-limit:]

    def clear_session(self, session_id: str) -> None:
        self.records = [record for record in self.records if record[0] != session_id]


class FakeTraceLogger:
    """收集 trace 写入结果，便于断言。"""

    def __init__(self) -> None:
        self.records: list[TraceRecord] = []
        self.error_records: list[tuple[TraceRecord, Exception]] = []

    def record(self, trace_record: TraceRecord) -> None:
        self.records.append(trace_record)

    def record_error(self, trace_record: TraceRecord, exc: Exception) -> None:
        self.error_records.append((trace_record, exc))


class TodoHandlers:
    """测试用待办工具处理器。"""

    def add_todo(self, task: str) -> dict[str, object]:
        return {"todo_id": 1, "task": task}


class OrchestratorTestCase(unittest.TestCase):
    """验证编排层在成功和失败场景下的固定行为。"""

    def _build_orchestrator(self, raw_output: str) -> tuple[Orchestrator, FakeTraceLogger]:
        tool_registry = ToolRegistry()
        tool_registry.register(
            ToolDefinition(
                name="add_todo",
                description="新增一条待办事项。",
                input_schema={"task": "字符串"},
                handler=TodoHandlers().add_todo,
            )
        )

        trace_logger = FakeTraceLogger()
        orchestrator = Orchestrator(
            session_manager=SessionManager(),
            message_store=InMemoryMessageStore(),
            prompt_builder=PromptBuilder(history_limit=6),
            llm_client=FakeLLMClient(raw_output),
            decision_parser=DecisionParser(),
            tool_registry=tool_registry,
            tool_executor=ToolExecutor(tool_registry=tool_registry),
            response_formatter=ResponseFormatter(),
            trace_logger=trace_logger,  # type: ignore[arg-type]
            history_limit=6,
        )
        return orchestrator, trace_logger

    def test_handle_user_input_returns_direct_answer(self) -> None:
        """模型直接回答时应原样返回答案并记录正常 trace。"""

        orchestrator, trace_logger = self._build_orchestrator('{"action":"respond","answer":"你好"}')

        response = orchestrator.handle_user_input("打个招呼")

        self.assertEqual(response, "你好")
        self.assertEqual(len(trace_logger.records), 1)
        self.assertEqual(trace_logger.records[0].action_type, "respond")

    def test_handle_user_input_formats_tool_result(self) -> None:
        """工具执行成功时应走固定模板文案。"""

        orchestrator, trace_logger = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"add_todo","arguments":{"task":"买牛奶"}}'
        )

        response = orchestrator.handle_user_input("帮我记个待办")

        self.assertEqual(response, "已记录待办：买牛奶")
        self.assertEqual(len(trace_logger.records), 1)
        self.assertEqual(trace_logger.records[0].tool_name, "add_todo")

    def test_handle_user_input_returns_fixed_message_for_invalid_json(self) -> None:
        """模型输出非法 JSON 时应返回固定错误文案。"""

        orchestrator, trace_logger = self._build_orchestrator("not json")

        response = orchestrator.handle_user_input("随便说点什么")

        self.assertEqual(response, "模型输出解析失败，请重试")
        self.assertEqual(len(trace_logger.error_records), 1)
        self.assertEqual(trace_logger.error_records[0][0].final_response, "模型输出解析失败，请重试")

    def test_handle_user_input_returns_fixed_message_for_invalid_tool_args(self) -> None:
        """工具参数不完整时应返回固定参数错误文案。"""

        orchestrator, trace_logger = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"add_todo","arguments":{}}'
        )

        response = orchestrator.handle_user_input("帮我记个待办")

        self.assertEqual(response, "工具参数不合法")
        self.assertEqual(len(trace_logger.error_records), 1)
        self.assertEqual(trace_logger.error_records[0][0].tool_name, "add_todo")


if __name__ == "__main__":
    unittest.main()
