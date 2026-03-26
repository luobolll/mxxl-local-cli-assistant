"""模型决策结果解析器。"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.schemas.models import ActionDecision


class DecisionParser:
    """把模型原始输出解析成统一的动作对象。"""

    def parse(self, raw_output: str) -> ActionDecision:
        """解析模型输出文本，并校验它是否符合动作协议。"""

        json_text = self._extract_json(raw_output)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"模型输出不是合法 JSON：{exc}") from exc

        try:
            return ActionDecision.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"模型输出不符合动作协议：{exc}") from exc

    def _extract_json(self, raw_output: str) -> str:
        """从模型输出中提取 JSON 部分。

        有些模型会把 JSON 包在 Markdown 代码块里，这里先做一层兼容。
        """

        text = raw_output.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1]).strip()
        return text
