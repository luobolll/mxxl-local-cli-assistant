"""PromptBuilder 测试。

这些测试用来保证系统提示词持续满足架构文档里的固定约束，
避免后续修改把工具选择规则和 JSON 协议提示删掉。
"""

from __future__ import annotations

import unittest

from app.prompts.prompt_builder import PromptBuilder
from app.schemas.models import Message


class PromptBuilderTestCase(unittest.TestCase):
    """验证 prompt 是否包含关键约束。"""

    def test_build_contains_required_protocol_and_tool_rules(self) -> None:
        """生成的 prompt 应包含动作协议和工具路由约束。"""

        builder = PromptBuilder(history_limit=6)
        prompt = builder.build(
            messages=[
                Message(role="user", content="帮我记住我喜欢喝咖啡"),
                Message(role="assistant", content="好的"),
            ],
            tool_description="工具名：save_memory",
        )

        self.assertIn("你只能输出合法 JSON", prompt)
        self.assertIn("你每一轮只能选择一个动作", prompt)
        self.assertIn("action 只能是 respond 或 tool_call", prompt)
        self.assertIn("如果用户要记录信息，优先调用 save_memory", prompt)
        self.assertIn("如果用户要查看记忆，调用 get_memory", prompt)
        self.assertIn("如果用户要记录待办，调用 add_todo", prompt)
        self.assertIn("如果用户要查看待办，调用 list_todos", prompt)
        self.assertIn("用户：帮我记住我喜欢喝咖啡", prompt)
        self.assertIn("助手：好的", prompt)

    def test_build_system_and_user_prompt_are_split_for_chat_api(self) -> None:
        """system 和 user 提示词应能分别构造。"""

        builder = PromptBuilder(history_limit=6)
        system_prompt = builder.build_system_prompt("工具名：save_memory")
        user_prompt = builder.build_user_prompt(
            [
                Message(role="user", content="请记住我喜欢喝咖啡"),
                Message(role="assistant", content="好的"),
            ]
        )

        self.assertIn("如果用户明确要求调用某个工具，就必须返回 tool_call", system_prompt)
        self.assertIn("两个合法输出示例", system_prompt)
        self.assertIn("最近对话如下：", user_prompt)
        self.assertIn("用户：请记住我喜欢喝咖啡", user_prompt)


if __name__ == "__main__":
    unittest.main()
