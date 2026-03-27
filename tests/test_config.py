"""配置加载测试。"""

from __future__ import annotations

import os
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from app.config import Settings


class SettingsTestCase(unittest.TestCase):
    """验证环境变量和 .env 文件的读取逻辑。"""

    def setUp(self) -> None:
        self.test_root = Path("data") / f"test-config-{uuid.uuid4().hex}"
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.env_path = self.test_root / ".env"

    def test_from_env_loads_values_from_env_file(self) -> None:
        """当系统环境变量缺失时，应从 .env 文件补全。"""

        self.env_path.write_text(
            "\n".join(
                [
                    "ZHIPUAI_API_KEY=file-key",
                    "ZHIPUAI_BASE_URL=https://example.com/v4/chat/completions",
                    "ZHIPUAI_MODEL=glm-file",
                    "AGENT_DB_PATH=data/custom-agent.db",
                ]
            ),
            encoding="utf-8",
        )

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env(env_path=self.env_path)

        self.assertEqual(settings.zhipu_api_key, "file-key")
        self.assertEqual(settings.zhipu_base_url, "https://example.com/v4/chat/completions")
        self.assertEqual(settings.zhipu_model, "glm-file")
        self.assertEqual(settings.db_path, Path("data/custom-agent.db"))

    def test_from_env_keeps_real_environment_priority(self) -> None:
        """系统环境变量应覆盖 .env 中的同名配置。"""

        self.env_path.write_text(
            "\n".join(
                [
                    "ZHIPUAI_API_KEY=file-key",
                    "ZHIPUAI_MODEL=glm-file",
                ]
            ),
            encoding="utf-8",
        )

        with patch.dict(
            os.environ,
            {
                "ZHIPUAI_API_KEY": "env-key",
                "ZHIPUAI_MODEL": "glm-env",
            },
            clear=True,
        ):
            settings = Settings.from_env(env_path=self.env_path)

        self.assertEqual(settings.zhipu_api_key, "env-key")
        self.assertEqual(settings.zhipu_model, "glm-env")


if __name__ == "__main__":
    unittest.main()
