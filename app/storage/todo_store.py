"""待办事项存储层。"""

from __future__ import annotations

from app.schemas.models import utc_now_iso
from app.storage.sqlite import SQLiteManager


class TodoStore:
    """负责读写待办事项。"""

    def __init__(self, sqlite_manager: SQLiteManager) -> None:
        self.sqlite_manager = sqlite_manager

    def add_todo(self, task: str) -> dict[str, object]:
        """新增一条待办事项。"""

        now = utc_now_iso()
        with self.sqlite_manager.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO todos (task, status, created_at, updated_at)
                VALUES (?, 'open', ?, ?)
                """,
                (task, now, now),
            )
            todo_id = cursor.lastrowid
        return {"todo_id": int(todo_id), "task": task}

    def list_open_todos(self) -> list[dict[str, object]]:
        """列出所有未完成的待办事项。"""

        with self.sqlite_manager.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, task, status, created_at, updated_at
                FROM todos
                WHERE status = 'open'
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "task": str(row["task"]),
                "status": str(row["status"]),
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]
