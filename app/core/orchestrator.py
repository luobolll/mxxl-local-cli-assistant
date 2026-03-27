"""系统主编排器。

这个文件负责把“会话、提示词、模型调用、工具执行、结果记录”串成一条完整流程。
它是系统的控制中心，但不直接实现具体工具，也不直接写 SQL。
"""

from __future__ import annotations

from app.core.errors import AssistantError, ModelOutputParseError, ModelOutputSchemaError
from app.core.response_formatter import ResponseFormatter
from app.core.session_manager import SessionManager
from app.core.tool_executor import ToolExecutor
from app.core.tool_request_router import ToolRequestRouter
from app.core.tool_registry import ToolRegistry
from app.llm.llm_client import ZhipuLLMClient
from app.observability.trace_logger import TraceLogger
from app.parsers.decision_parser import DecisionParser
from app.prompts.prompt_builder import PromptBuilder
from app.schemas.models import ActionDecision, ToolCall, TraceRecord
from app.storage.message_store import MessageStore


class Orchestrator:
    """协调一次用户请求从输入到输出的完整过程。"""

    def __init__(
        self,
        session_manager: SessionManager,
        message_store: MessageStore,
        prompt_builder: PromptBuilder,
        llm_client: ZhipuLLMClient,
        decision_parser: DecisionParser,
        tool_request_router: ToolRequestRouter,
        tool_registry: ToolRegistry,
        tool_executor: ToolExecutor,
        response_formatter: ResponseFormatter,
        trace_logger: TraceLogger,
        history_limit: int,
    ) -> None:
        self.session_manager = session_manager
        self.message_store = message_store
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.decision_parser = decision_parser
        self.tool_request_router = tool_request_router
        self.tool_registry = tool_registry
        self.tool_executor = tool_executor
        self.response_formatter = response_formatter
        self.trace_logger = trace_logger
        self.history_limit = history_limit

    def handle_user_input(self, user_input: str) -> str:
        """处理一条用户输入，并返回最终显示给用户的文本。"""

        session_id = self.session_manager.get_current_session_id()

        # 先把用户输入写入消息表，保证会话历史是完整的。
        self.message_store.add_message(session_id=session_id, role="user", content=user_input)

        # 读取最近历史消息，用来构造本轮模型上下文。
        recent_messages = self.message_store.list_recent_messages(
            session_id=session_id,
            limit=self.history_limit,
        )
        tool_description = self.tool_registry.render_prompt_description()
        system_prompt = self.prompt_builder.build_system_prompt(tool_description=tool_description)
        user_prompt = self.prompt_builder.build_user_prompt(messages=recent_messages)
        prompt_text = self.prompt_builder.build(
            messages=recent_messages,
            tool_description=tool_description,
        )
        routed_tool_call = self.tool_request_router.route(user_input)

        # 这些变量先定义出来，是为了无论成功还是失败，trace 里都能留下完整记录。
        raw_model_output = ""
        final_response = ""
        action_type = "error"
        tool_name = None
        tool_args_json = None
        tool_result_json = None

        try:
            # 第一步：让模型根据 prompt 输出动作决策。
            raw_model_output = self.llm_client.complete(system_prompt, user_prompt)
            try:
                decision = self.decision_parser.parse(raw_model_output)
            except (ModelOutputParseError, ModelOutputSchemaError):
                if routed_tool_call is None:
                    raise
                decision = None

            tool_call = self._resolve_tool_call(decision=decision, routed_tool_call=routed_tool_call)

            if tool_call is None:
                action_type = decision.action if decision is not None else action_type
                # 模型决定直接回答时，不进入工具执行流程。
                final_response = self.response_formatter.format_direct_answer(decision.answer or "")
            else:
                action_type = "tool_call"
                tool_name = tool_call.tool_name
                tool_args_json = self.response_formatter.to_json_text(tool_call.arguments)
                tool_result = self.tool_executor.execute(tool_call)
                tool_result_json = self.response_formatter.to_json_text(tool_result.model_dump())
                final_response = self.response_formatter.format_tool_result(tool_result)

            # 把系统最终返回给用户的结果也写入会话历史，方便后续上下文连续。
            self.message_store.add_message(
                session_id=session_id,
                role="assistant",
                content=final_response,
            )

            trace_record = TraceRecord(
                session_id=session_id,
                user_input=user_input,
                prompt_text=prompt_text,
                model_output=raw_model_output,
                action_type=action_type,
                tool_name=tool_name,
                tool_args_json=tool_args_json,
                tool_result_json=tool_result_json,
                final_response=final_response,
            )
            self.trace_logger.record(trace_record)
            return final_response
        except AssistantError as exc:
            # 已知错误类型走固定用户文案，同时把更具体的细节留给日志和 trace。
            final_response = self.response_formatter.format_error(exc.user_message)
            self.message_store.add_message(
                session_id=session_id,
                role="assistant",
                content=final_response,
            )
            trace_record = TraceRecord(
                session_id=session_id,
                user_input=user_input,
                prompt_text=prompt_text,
                model_output=raw_model_output,
                action_type=action_type,
                tool_name=tool_name,
                tool_args_json=tool_args_json,
                tool_result_json=tool_result_json,
                final_response=final_response,
            )
            self.trace_logger.record_error(trace_record, exc)
            return final_response
        except Exception as exc:
            # 兜底异常不向用户暴露内部细节，但仍然完整记录 trace 和异常栈。
            final_response = self.response_formatter.format_error("请求处理失败，请重试")
            self.message_store.add_message(
                session_id=session_id,
                role="assistant",
                content=final_response,
            )
            trace_record = TraceRecord(
                session_id=session_id,
                user_input=user_input,
                prompt_text=prompt_text,
                model_output=raw_model_output,
                action_type=action_type,
                tool_name=tool_name,
                tool_args_json=tool_args_json,
                tool_result_json=tool_result_json,
                final_response=final_response,
            )
            self.trace_logger.record_error(trace_record, exc)
            return final_response

    def _resolve_tool_call(
        self,
        decision: ActionDecision | None,
        routed_tool_call: ToolCall | None,
    ) -> ToolCall | None:
        """在模型决策和显式工具请求之间选择最终工具调用。

        当用户已经明确指定工具名时，优先使用程序侧解析出的 ToolCall，
        避免真实模型把工具请求错误地回答成自然语言。
        """

        if routed_tool_call is not None:
            return routed_tool_call

        if decision is not None and decision.action == "tool_call":
            return ToolCall(tool_name=decision.tool_name or "", arguments=decision.arguments)

        return None

    def clear_session(self) -> str:
        """清空当前会话消息，并生成一个新的会话 ID。"""

        old_session_id = self.session_manager.get_current_session_id()
        self.message_store.clear_session(old_session_id)
        return self.session_manager.reset_session()
