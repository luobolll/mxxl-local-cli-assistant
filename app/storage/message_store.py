"""消息存储层。"""

from __future__ import annotations

from app.schemas.models import Message
from app.storage.sqlite import SQLiteManager


class MessageStore:
    """负责读写会话消息历史。"""

    def __init__(self, sqlite_manager: SQLiteManager) -> None:
        self.sqlite_manager = sqlite_manager

    def add_message(self, session_id: str, role: str, content: str) -> Message:
        """新增一条消息记录。"""

        message = Message(role=role, content=content)
        with self.sqlite_manager.connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, message.created_at),
            )
        return message

    def list_recent_messages(self, session_id: str, limit: int) -> list[Message]:
        """读取某个会话最近的消息列表。"""

        with self.sqlite_manager.connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        messages = [Message(role=row["role"], content=row["content"], created_at=row["created_at"]) for row in rows]
        # SQL 里按倒序查是为了更容易拿到“最近几条”，返回前再反转回正常时间顺序。
        messages.reverse()
        return messages

    def clear_session(self, session_id: str) -> None:
        """删除某个会话的全部消息。"""

        with self.sqlite_manager.connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
