"""智谱客户端测试。"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from app.llm.llm_client import ZhipuLLMClient


class ZhipuLLMClientTestCase(unittest.TestCase):
    """验证智谱 API 调用封装的关键行为。"""

    def setUp(self) -> None:
        self.client = ZhipuLLMClient(
            api_key="test-key",
            base_url="https://example.com/chat/completions",
            model="glm-test",
        )

    def test_complete_returns_message_content(self) -> None:
        """成功响应时应提取 choices[0].message.content。"""

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"action":"respond","answer":"你好"}',
                    }
                }
            ]
        }

        with patch("app.llm.llm_client.requests.post", return_value=response) as mock_post:
            result = self.client.complete("你好")

        self.assertEqual(result, '{"action":"respond","answer":"你好"}')
        self.assertEqual(mock_post.call_args.kwargs["json"]["model"], "glm-test")

    def test_complete_raises_runtime_error_on_request_failure(self) -> None:
        """网络请求失败时应抛出可读错误。"""

        with patch(
            "app.llm.llm_client.requests.post",
            side_effect=requests.RequestException("network down"),
        ):
            with self.assertRaises(RuntimeError) as context:
                self.client.complete("你好")

        self.assertIn("调用智谱接口失败", str(context.exception))

    def test_complete_raises_runtime_error_on_invalid_response_shape(self) -> None:
        """返回结构不符合预期时应抛出可读错误。"""

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"choices": []}

        with patch("app.llm.llm_client.requests.post", return_value=response):
            with self.assertRaises(RuntimeError) as context:
                self.client.complete("你好")

        self.assertIn("模型服务返回格式不符合预期", str(context.exception))


if __name__ == "__main__":
    unittest.main()
