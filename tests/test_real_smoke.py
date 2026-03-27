"""真实智谱联调烟雾测试。

这个测试默认跳过，只有在本地明确设置 RUN_REAL_ZHIPU_SMOKE=1 时才执行。
用途是验证 MVP 在真实模型环境下至少能跑通一轮直接回答和一轮工具调用。
"""

from __future__ import annotations

import os
import sqlite3
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from app.cli.main import build_orchestrator


@unittest.skipUnless(os.getenv("RUN_REAL_ZHIPU_SMOKE") == "1", "未启用真实智谱联调")
class RealZhipuSmokeTestCase(unittest.TestCase):
    """在真实智谱环境下验证最小闭环。"""

    def setUp(self) -> None:
        self.test_root = Path("data") / f"real-smoke-{uuid.uuid4().hex}"
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.test_root / "agent.db"

    def test_real_direct_answer_and_all_tools(self) -> None:
        """至少跑通一轮直接回答，并验证四个工具都真正落库。"""

        with patch.dict(os.environ, {"AGENT_DB_PATH": str(self.db_path)}, clear=False):
            orchestrator = build_orchestrator()

            direct_response = orchestrator.handle_user_input("请用一句中文介绍你是一个本地命令行个人助手。")
            save_memory_response = orchestrator.handle_user_input(
                "你必须调用 save_memory 工具，把 key 设为 favorite_drink，把 value 设为 coffee。不要直接回答。"
            )
            get_memory_response = orchestrator.handle_user_input(
                "你必须调用 get_memory 工具，查询 favorite_drink。不要直接回答。"
            )
            add_todo_response = orchestrator.handle_user_input(
                "你必须调用 add_todo 工具，记录待办：明天买牛奶。不要直接回答。"
            )
            list_todos_response = orchestrator.handle_user_input(
                "你必须调用 list_todos 工具，列出当前所有待办。不要直接回答。"
            )

        self.assertTrue(direct_response.strip())
        self.assertEqual(save_memory_response, "已记住：favorite_drink = coffee")
        self.assertEqual(get_memory_response, "已找到记忆：favorite_drink = coffee")
        self.assertEqual(add_todo_response, "已记录待办：明天买牛奶")
        self.assertIn("当前待办：", list_todos_response)
        self.assertIn("明天买牛奶", list_todos_response)

        conn = sqlite3.connect(self.db_path)
        try:
            memory_row = conn.execute(
                "SELECT key, value FROM memories WHERE key = ?",
                ("favorite_drink",),
            ).fetchone()
            todo_rows = conn.execute(
                "SELECT task, status FROM todos ORDER BY id ASC",
            ).fetchall()
            trace_count = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
        finally:
            conn.close()

        self.assertEqual(memory_row, ("favorite_drink", "coffee"))
        self.assertEqual(todo_rows, [("明天买牛奶", "open")])
        self.assertEqual(trace_count, 5)


if __name__ == "__main__":
    unittest.main()
