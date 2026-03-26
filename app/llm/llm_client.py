"""大模型调用封装。

当前版本只接智谱 API。后续如果更换模型提供商，优先改这个目录，
而不是把网络请求散落到业务代码里。
"""

from __future__ import annotations

from typing import Any

import requests


class ZhipuLLMClient:
    """封装一次智谱对话补全请求。"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete(self, prompt: str) -> str:
        """向模型发送 prompt，并返回模型文本输出。"""

        if not self.api_key:
            raise RuntimeError("缺少智谱接口密钥，请先设置 ZHIPUAI_API_KEY。")

        # 当前骨架只做最直接的一轮对话调用：把完整 prompt 作为一条 user 消息发给模型。
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"调用智谱接口失败：{exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("模型服务返回的内容不是合法 JSON。") from exc
        return self._extract_content(data)

    def _extract_content(self, payload: dict[str, Any]) -> str:
        """从模型返回结果里提取真正的文本内容。"""

        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("模型服务返回格式不符合预期。") from exc
