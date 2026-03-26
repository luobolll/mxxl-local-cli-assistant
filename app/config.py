"""读取项目运行配置。

这个文件只负责把环境变量整理成一个统一的配置对象，
不负责发起网络请求，也不负责初始化数据库。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "agent.db"
DEFAULT_ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_ZHIPU_MODEL = "glm-4-flash"


@dataclass(frozen=True)
class Settings:
    """保存运行时需要用到的配置项。

    这里使用 dataclass 是为了把零散配置集中到一个对象里，
    后续传递给其他模块时更清晰。
    """

    zhipu_api_key: str
    zhipu_base_url: str
    zhipu_model: str
    db_path: Path
    history_limit: int = 6
    request_timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量读取配置并生成 Settings 对象。"""

        # 数据库路径允许通过环境变量覆盖，方便后面切换到别的文件位置。
        db_path = Path(os.getenv("AGENT_DB_PATH", str(DEFAULT_DB_PATH)))
        return cls(
            zhipu_api_key=os.getenv("ZHIPUAI_API_KEY", "").strip(),
            zhipu_base_url=os.getenv("ZHIPUAI_BASE_URL", DEFAULT_ZHIPU_BASE_URL).strip(),
            zhipu_model=os.getenv("ZHIPUAI_MODEL", DEFAULT_ZHIPU_MODEL).strip(),
            db_path=db_path,
        )

    def validate(self) -> None:
        """检查当前配置是否满足最基本的运行条件。"""

        if not self.zhipu_api_key:
            raise ValueError("环境变量中缺少 ZHIPUAI_API_KEY。")
