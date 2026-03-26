"""命令行入口。

这个文件负责两件事：
1. 组装项目运行所需的依赖对象
2. 启动命令行循环，接收用户输入

它不负责具体业务流程编排，业务流程统一交给 Orchestrator。
"""

from __future__ import annotations

from app.config import Settings
from app.core.orchestrator import Orchestrator
from app.core.response_formatter import ResponseFormatter
from app.core.session_manager import SessionManager
from app.core.tool_executor import ToolExecutor
from app.core.tool_registry import ToolDefinition, ToolRegistry
from app.llm.llm_client import ZhipuLLMClient
from app.observability.trace_logger import TraceLogger
from app.parsers.decision_parser import DecisionParser
from app.prompts.prompt_builder import PromptBuilder
from app.storage.memory_store import MemoryStore
from app.storage.message_store import MessageStore
from app.storage.sqlite import SQLiteManager
from app.storage.todo_store import TodoStore
from app.storage.trace_store import TraceStore
from app.tools.memory_tools import MemoryTools
from app.tools.todo_tools import TodoTools


def build_orchestrator() -> Orchestrator:
    """创建并组装一个可运行的 Orchestrator 实例。

    这里集中完成依赖注入，目的是让 main 函数本身保持简单，
    也方便后面替换某个模块实现时只改一个地方。
    """

    settings = Settings.from_env()
    settings.validate()

    # 先准备数据库和各类 Store。Store 负责和 SQLite 打交道。
    sqlite_manager = SQLiteManager(settings.db_path)
    sqlite_manager.initialize()

    message_store = MessageStore(sqlite_manager)
    todo_store = TodoStore(sqlite_manager)
    memory_store = MemoryStore(sqlite_manager)
    trace_store = TraceStore(sqlite_manager)

    todo_tools = TodoTools(todo_store)
    memory_tools = MemoryTools(memory_store)

    # 工具注册表告诉系统：有哪些工具、工具名是什么、实际对应哪个函数。
    tool_registry = ToolRegistry()
    tool_registry.register(
        ToolDefinition(
            name="add_todo",
            description="新增一条待办事项。",
            input_schema={"task": "字符串"},
            handler=todo_tools.add_todo,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="list_todos",
            description="列出当前所有未完成的待办事项。",
            input_schema={},
            handler=todo_tools.list_todos,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="save_memory",
            description="保存一条结构化记忆键值对。",
            input_schema={"key": "字符串", "value": "字符串"},
            handler=memory_tools.save_memory,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="get_memory",
            description="按键读取之前保存的记忆。",
            input_schema={"key": "字符串"},
            handler=memory_tools.get_memory,
        )
    )

    return Orchestrator(
        session_manager=SessionManager(),
        message_store=message_store,
        prompt_builder=PromptBuilder(history_limit=settings.history_limit),
        llm_client=ZhipuLLMClient(
            api_key=settings.zhipu_api_key,
            base_url=settings.zhipu_base_url,
            model=settings.zhipu_model,
            timeout_seconds=settings.request_timeout_seconds,
        ),
        decision_parser=DecisionParser(),
        tool_registry=tool_registry,
        tool_executor=ToolExecutor(tool_registry=tool_registry),
        response_formatter=ResponseFormatter(),
        trace_logger=TraceLogger(trace_store=trace_store),
        history_limit=settings.history_limit,
    )


def main() -> None:
    """启动命令行助手。"""

    orchestrator = build_orchestrator()

    print("本地命令行助手已启动。")
    print("输入 /help 查看可用命令。")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue

        # 这里先处理命令行自己的控制命令，不进入大模型流程。
        if user_input == "/exit":
            print("程序已退出。")
            return

        if user_input == "/help":
            print("/help  查看帮助")
            print("/clear 清空当前会话历史")
            print("/exit  退出程序")
            continue

        if user_input == "/clear":
            orchestrator.clear_session()
            print("当前会话已清空。")
            continue

        # 普通自然语言输入统一交给编排核心处理。
        response = orchestrator.handle_user_input(user_input)
        print(response)


if __name__ == "__main__":
    main()
