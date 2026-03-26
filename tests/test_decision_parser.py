"""DecisionParser 测试。"""

from __future__ import annotations

import unittest

from app.core.errors import ModelOutputParseError, ModelOutputSchemaError
from app.parsers.decision_parser import DecisionParser


class DecisionParserTestCase(unittest.TestCase):
    """验证模型输出解析失败时的固定错误语义。"""

    def setUp(self) -> None:
        self.parser = DecisionParser()

    def test_parse_raises_fixed_error_for_invalid_json(self) -> None:
        """非法 JSON 应映射成固定的解析失败提示。"""

        with self.assertRaises(ModelOutputParseError) as context:
            self.parser.parse("这不是 JSON")

        self.assertEqual(context.exception.user_message, "模型输出解析失败，请重试")

    def test_parse_raises_fixed_error_for_incomplete_fields(self) -> None:
        """字段不完整时应映射成固定的协议错误提示。"""

        with self.assertRaises(ModelOutputSchemaError) as context:
            self.parser.parse('{"action":"tool_call","tool_name":"add_todo"}')

        self.assertEqual(context.exception.user_message, "模型输出字段不完整，请重试")


if __name__ == "__main__":
    unittest.main()
