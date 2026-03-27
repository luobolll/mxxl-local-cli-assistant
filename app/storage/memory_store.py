"""结构化记忆存储层。"""

from __future__ import annotations

from app.schemas.models import utc_now_iso
from app.storage.sqlite import SQLiteManager


class MemoryStore:
    """负责读写长期记忆键值对。"""

    def __init__(self, sqlite_manager: SQLiteManager) -> None:
        self.sqlite_manager = sqlite_manager

    def upsert_memory(self, key: str, value: str) -> dict[str, str]:
        """保存或更新一条记忆。"""

        now = utc_now_iso()
        with self.sqlite_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, now, now),
            )
        return {"key": key, "value": value}

    def get_memory(self, key: str) -> str | None:
        """按 key 查询记忆，如果不存在则返回 None。"""

        with self.sqlite_manager.connection() as conn:
            row = conn.execute(
                "SELECT value FROM memories WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return str(row["value"])
