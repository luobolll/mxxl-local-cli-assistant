"""SQLite 存储层测试。

这些测试直接使用真实 SQLite 文件，验证 MVP 要求的数据落盘行为，
包括消息、待办、记忆、trace 和跨重启持久化。
"""

from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from app.schemas.models import TraceRecord
from app.storage.memory_store import MemoryStore
from app.storage.message_store import MessageStore
from app.storage.sqlite import SQLiteManager
from app.storage.todo_store import TodoStore
from app.storage.trace_store import TraceStore


class SQLiteStoreTestCase(unittest.TestCase):
    """验证 SQLite Store 层的真实读写。"""

    def setUp(self) -> None:
        self.test_root = Path("data") / f"test-storage-{uuid.uuid4().hex}"
        self.db_path = self.test_root / "agent.db"
        self.sqlite_manager = SQLiteManager(self.db_path)
        self.sqlite_manager.initialize()

    def test_message_store_add_list_and_clear_session(self) -> None:
        """消息写入、读取和清空应全部生效。"""

        message_store = MessageStore(self.sqlite_manager)

        message_store.add_message("session-1", "user", "第一句")
        message_store.add_message("session-1", "assistant", "第二句")
        message_store.add_message("session-2", "user", "第三句")

        recent_messages = message_store.list_recent_messages("session-1", limit=6)

        self.assertEqual([message.content for message in recent_messages], ["第一句", "第二句"])

        message_store.clear_session("session-1")

        self.assertEqual(message_store.list_recent_messages("session-1", limit=6), [])
        self.assertEqual(len(message_store.list_recent_messages("session-2", limit=6)), 1)

    def test_todo_memory_and_trace_are_persisted_across_new_manager(self) -> None:
        """待办、记忆和 trace 应跨新的 SQLiteManager 实例持续存在。"""

        todo_store = TodoStore(self.sqlite_manager)
        memory_store = MemoryStore(self.sqlite_manager)
        trace_store = TraceStore(self.sqlite_manager)

        todo_result = todo_store.add_todo("买牛奶")
        memory_store.upsert_memory("favorite_drink", "coffee")
        trace_store.add_trace(
            TraceRecord(
                session_id="session-1",
                user_input="帮我记个待办",
                prompt_text="prompt",
                model_output='{"action":"tool_call"}',
                action_type="tool_call",
                tool_name="add_todo",
                tool_args_json=json.dumps({"task": "买牛奶"}, ensure_ascii=False),
                tool_result_json=json.dumps(todo_result, ensure_ascii=False),
                final_response="已记录待办：买牛奶",
            )
        )

        reloaded_manager = SQLiteManager(self.db_path)
        reloaded_todo_store = TodoStore(reloaded_manager)
        reloaded_memory_store = MemoryStore(reloaded_manager)

        self.assertEqual(reloaded_todo_store.list_open_todos()[0]["task"], "买牛奶")
        self.assertEqual(reloaded_memory_store.get_memory("favorite_drink"), "coffee")

        with reloaded_manager.connection() as conn:
            message_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            todo_count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
            memory_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            trace_count = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]

        self.assertEqual(message_count, 0)
        self.assertEqual(todo_count, 1)
        self.assertEqual(memory_count, 1)
        self.assertEqual(trace_count, 1)


if __name__ == "__main__":
    unittest.main()
