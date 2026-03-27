"""CLI 入口测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.cli.main import main, run_cli_loop


class FakeOrchestrator:
    """用于 CLI 测试的假编排器。"""

    def __init__(self) -> None:
        self.handled_inputs: list[str] = []
        self.clear_called = 0

    def handle_user_input(self, user_input: str) -> str:
        self.handled_inputs.append(user_input)
        return f"响应：{user_input}"

    def clear_session(self) -> str:
        self.clear_called += 1
        return "new-session-id"


class CLITestCase(unittest.TestCase):
    """验证 CLI 的控制命令和普通输入行为。"""

    def test_run_cli_loop_handles_help_clear_and_exit(self) -> None:
        """CLI 应正确处理 /help、/clear 和 /exit。"""

        orchestrator = FakeOrchestrator()
        outputs: list[str] = []
        inputs = iter(["/help", "/clear", "/exit"])

        run_cli_loop(orchestrator, input_func=lambda _: next(inputs), output_func=outputs.append)

        self.assertEqual(outputs[0], "本地命令行助手已启动。")
        self.assertEqual(outputs[1], "输入 /help 查看可用命令。")
        self.assertIn("/help  查看帮助", outputs)
        self.assertIn("当前会话已清空。", outputs)
        self.assertEqual(outputs[-1], "程序已退出。")
        self.assertEqual(orchestrator.clear_called, 1)

    def test_run_cli_loop_forwards_normal_user_input(self) -> None:
        """普通输入应交给 Orchestrator 处理。"""

        orchestrator = FakeOrchestrator()
        outputs: list[str] = []
        inputs = iter(["你好", "/exit"])

        run_cli_loop(orchestrator, input_func=lambda _: next(inputs), output_func=outputs.append)

        self.assertEqual(orchestrator.handled_inputs, ["你好"])
        self.assertIn("响应：你好", outputs)

    def test_run_cli_loop_exits_on_eof(self) -> None:
        """EOF 时应优雅退出，而不是抛出异常。"""

        orchestrator = FakeOrchestrator()
        outputs: list[str] = []

        def raise_eof(_: str) -> str:
            raise EOFError

        run_cli_loop(orchestrator, input_func=raise_eof, output_func=outputs.append)

        self.assertEqual(outputs[-1], "程序已退出。")

    def test_main_prints_startup_failure_message(self) -> None:
        """启动依赖构建失败时应打印简洁错误。"""

        outputs: list[str] = []

        with patch("app.cli.main.build_orchestrator", side_effect=ValueError("环境变量中缺少 ZHIPUAI_API_KEY。")):
            with patch("builtins.print", side_effect=outputs.append):
                main()

        self.assertEqual(outputs, ["启动失败：环境变量中缺少 ZHIPUAI_API_KEY。"])


if __name__ == "__main__":
    unittest.main()
