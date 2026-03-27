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


class ToolHandlers:
    """测试用工具处理器集合。"""

    def __init__(self) -> None:
        self.todos: list[str] = []
        self.memories: dict[str, str] = {}

    def add_todo(self, task: str) -> dict[str, object]:
        self.todos.append(task)
        return {"todo_id": len(self.todos), "task": task}

    def list_todos(self) -> dict[str, list[dict[str, object]]]:
        return {
            "items": [
                {"id": index, "task": task, "status": "open"}
                for index, task in enumerate(self.todos, start=1)
            ]
        }

    def save_memory(self, key: str, value: str) -> dict[str, str]:
        self.memories[key] = value
        return {"key": key, "value": value}

    def get_memory(self, key: str) -> dict[str, str | None]:
        return {"key": key, "value": self.memories.get(key)}

    def explode(self, task: str) -> dict[str, object]:
        raise RuntimeError("模拟工具异常")


class OrchestratorTestCase(unittest.TestCase):
    """验证编排层在成功和失败场景下的固定行为。"""

    def _build_orchestrator(
        self,
        raw_output: str,
    ) -> tuple[Orchestrator, FakeTraceLogger, InMemoryMessageStore, ToolHandlers]:
        tool_registry = ToolRegistry()
        tool_handlers = ToolHandlers()
        tool_registry.register(
            ToolDefinition(
                name="add_todo",
                description="新增一条待办事项。",
                input_schema={"task": "字符串"},
                handler=tool_handlers.add_todo,
            )
        )
        tool_registry.register(
            ToolDefinition(
                name="list_todos",
                description="列出当前待办事项。",
                input_schema={},
                handler=tool_handlers.list_todos,
            )
        )
        tool_registry.register(
            ToolDefinition(
                name="save_memory",
                description="保存结构化记忆。",
                input_schema={"key": "字符串", "value": "字符串"},
                handler=tool_handlers.save_memory,
            )
        )
        tool_registry.register(
            ToolDefinition(
                name="get_memory",
                description="读取结构化记忆。",
                input_schema={"key": "字符串"},
                handler=tool_handlers.get_memory,
            )
        )
        tool_registry.register(
            ToolDefinition(
                name="explode",
                description="模拟失败工具。",
                input_schema={"task": "字符串"},
                handler=tool_handlers.explode,
            )
        )

        trace_logger = FakeTraceLogger()
        message_store = InMemoryMessageStore()
        orchestrator = Orchestrator(
            session_manager=SessionManager(),
            message_store=message_store,
            prompt_builder=PromptBuilder(history_limit=6),
            llm_client=FakeLLMClient(raw_output),
            decision_parser=DecisionParser(),
            tool_registry=tool_registry,
            tool_executor=ToolExecutor(tool_registry=tool_registry),
            response_formatter=ResponseFormatter(),
            trace_logger=trace_logger,  # type: ignore[arg-type]
            history_limit=6,
        )
        return orchestrator, trace_logger, message_store, tool_handlers

    def test_handle_user_input_returns_direct_answer(self) -> None:
        """模型直接回答时应原样返回答案并记录正常 trace。"""

        orchestrator, trace_logger, message_store, _ = self._build_orchestrator(
            '{"action":"respond","answer":"你好"}'
        )

        response = orchestrator.handle_user_input("打个招呼")

        self.assertEqual(response, "你好")
        self.assertEqual(len(trace_logger.records), 1)
        self.assertEqual(trace_logger.records[0].action_type, "respond")
        self.assertEqual(len(message_store.records), 2)

    def test_handle_user_input_formats_tool_result(self) -> None:
        """工具执行成功时应走固定模板文案。"""

        orchestrator, trace_logger, _, tool_handlers = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"add_todo","arguments":{"task":"买牛奶"}}'
        )

        response = orchestrator.handle_user_input("帮我记个待办")

        self.assertEqual(response, "已记录待办：买牛奶")
        self.assertEqual(len(trace_logger.records), 1)
        self.assertEqual(trace_logger.records[0].tool_name, "add_todo")
        self.assertEqual(tool_handlers.todos, ["买牛奶"])

    def test_handle_user_input_formats_list_todos_result(self) -> None:
        """列出待办时应走列表模板。"""

        orchestrator, _, _, tool_handlers = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"list_todos","arguments":{}}'
        )
        tool_handlers.todos = ["买牛奶", "买面包"]

        response = orchestrator.handle_user_input("看看待办")

        self.assertEqual(response, "当前待办：\n- [1] 买牛奶\n- [2] 买面包")

    def test_handle_user_input_formats_save_memory_result(self) -> None:
        """保存记忆时应返回固定文案。"""

        orchestrator, _, _, tool_handlers = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"save_memory","arguments":{"key":"name","value":"alice"}}'
        )

        response = orchestrator.handle_user_input("记住我的名字")

        self.assertEqual(response, "已记住：name = alice")
        self.assertEqual(tool_handlers.memories["name"], "alice")

    def test_handle_user_input_formats_get_memory_result(self) -> None:
        """读取记忆时应返回命中结果。"""

        orchestrator, _, _, tool_handlers = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"get_memory","arguments":{"key":"name"}}'
        )
        tool_handlers.memories["name"] = "alice"

        response = orchestrator.handle_user_input("我叫什么")

        self.assertEqual(response, "已找到记忆：name = alice")

    def test_handle_user_input_formats_missing_memory_result(self) -> None:
        """读取不存在的记忆时应返回未找到文案。"""

        orchestrator, _, _, _ = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"get_memory","arguments":{"key":"name"}}'
        )

        response = orchestrator.handle_user_input("我叫什么")

        self.assertEqual(response, "没有找到键为 name 的记忆")

    def test_handle_user_input_returns_fixed_message_for_invalid_json(self) -> None:
        """模型输出非法 JSON 时应返回固定错误文案。"""

        orchestrator, trace_logger, _, _ = self._build_orchestrator("not json")

        response = orchestrator.handle_user_input("随便说点什么")

        self.assertEqual(response, "模型输出解析失败，请重试")
        self.assertEqual(len(trace_logger.error_records), 1)
        self.assertEqual(trace_logger.error_records[0][0].final_response, "模型输出解析失败，请重试")

    def test_handle_user_input_returns_fixed_message_for_invalid_tool_args(self) -> None:
        """工具参数不完整时应返回固定参数错误文案。"""

        orchestrator, trace_logger, _, _ = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"add_todo","arguments":{}}'
        )

        response = orchestrator.handle_user_input("帮我记个待办")

        self.assertEqual(response, "工具参数不合法")
        self.assertEqual(len(trace_logger.error_records), 1)
        self.assertEqual(trace_logger.error_records[0][0].tool_name, "add_todo")

    def test_handle_user_input_returns_fixed_message_for_unknown_tool(self) -> None:
        """模型请求未知工具时应返回固定文案。"""

        orchestrator, trace_logger, _, _ = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"unknown_tool","arguments":{}}'
        )

        response = orchestrator.handle_user_input("调用未知工具")

        self.assertEqual(response, "请求的工具不存在")
        self.assertEqual(len(trace_logger.error_records), 1)

    def test_handle_user_input_returns_fixed_message_for_tool_execution_error(self) -> None:
        """工具执行异常时应返回固定文案。"""

        orchestrator, trace_logger, _, _ = self._build_orchestrator(
            '{"action":"tool_call","tool_name":"explode","arguments":{"task":"boom"}}'
        )

        response = orchestrator.handle_user_input("执行失败工具")

        self.assertEqual(response, "工具执行失败")
        self.assertEqual(len(trace_logger.error_records), 1)


if __name__ == "__main__":
    unittest.main()
