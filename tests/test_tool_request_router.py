"""显式工具请求路由器测试。"""

from __future__ import annotations

import unittest

from app.core.tool_request_router import ToolRequestRouter


class ToolRequestRouterTestCase(unittest.TestCase):
    """验证显式工具请求的兜底解析。"""

    def setUp(self) -> None:
        self.router = ToolRequestRouter()

    def test_route_save_memory_request(self) -> None:
        """显式 save_memory 请求应提取 key 和 value。"""

        tool_call = self.router.route(
            "你必须调用 save_memory 工具，把 key 设为 favorite_drink，把 value 设为 coffee。不要直接回答。"
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call.tool_name, "save_memory")
        self.assertEqual(tool_call.arguments, {"key": "favorite_drink", "value": "coffee"})

    def test_route_get_memory_request(self) -> None:
        """显式 get_memory 请求应提取 key。"""

        tool_call = self.router.route(
            "你必须调用 get_memory 工具，查询 favorite_drink。不要直接回答。"
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call.tool_name, "get_memory")
        self.assertEqual(tool_call.arguments, {"key": "favorite_drink"})

    def test_route_add_todo_request(self) -> None:
        """显式 add_todo 请求应提取待办内容。"""

        tool_call = self.router.route(
            "你必须调用 add_todo 工具，记录待办：明天买牛奶。不要直接回答。"
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call.tool_name, "add_todo")
        self.assertEqual(tool_call.arguments, {"task": "明天买牛奶"})

    def test_route_list_todos_request(self) -> None:
        """显式 list_todos 请求应返回无参数工具调用。"""

        tool_call = self.router.route(
            "你必须调用 list_todos 工具，列出当前所有待办。不要直接回答。"
        )

        self.assertIsNotNone(tool_call)
        self.assertEqual(tool_call.tool_name, "list_todos")
        self.assertEqual(tool_call.arguments, {})


if __name__ == "__main__":
    unittest.main()
