"""记忆工具实现。"""

from __future__ import annotations

from app.storage.memory_store import MemoryStore


class MemoryTools:
    """把记忆相关能力包装成可供工具执行器调用的方法。"""

    def __init__(self, memory_store: MemoryStore) -> None:
        self.memory_store = memory_store

    def save_memory(self, key: str, value: str) -> dict[str, str]:
        """保存一条结构化记忆。"""

        return self.memory_store.upsert_memory(key=key, value=value)

    def get_memory(self, key: str) -> dict[str, str | None]:
        """读取一条结构化记忆。"""

        return {"key": key, "value": self.memory_store.get_memory(key)}
