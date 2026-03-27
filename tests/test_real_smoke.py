"""真实智谱联调烟雾测试。

这个测试默认跳过，只有在本地明确设置 RUN_REAL_ZHIPU_SMOKE=1 时才执行。
用途是验证 MVP 在真实模型环境下至少能跑通一轮直接回答和一轮工具调用。
"""

from __future__ import annotations

import os
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

    def test_real_direct_answer_and_tool_call(self) -> None:
        """至少跑通一轮直接回答和一轮 save_memory 工具调用。"""

        with patch.dict(os.environ, {"AGENT_DB_PATH": str(self.db_path)}, clear=False):
            orchestrator = build_orchestrator()

            direct_response = orchestrator.handle_user_input("请用一句中文介绍你是一个本地命令行个人助手。")
            tool_response = orchestrator.handle_user_input(
                "请把我的偏好记录下来：favorite_drink = coffee。你必须调用 save_memory 工具，不要直接回答。"
            )

        self.assertTrue(direct_response.strip())
        self.assertTrue(tool_response.startswith("已记住：favorite_drink = coffee"))


if __name__ == "__main__":
    unittest.main()
