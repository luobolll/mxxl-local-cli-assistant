"""待办工具实现。"""

from __future__ import annotations

from app.storage.todo_store import TodoStore


class TodoTools:
    """把待办相关能力包装成可供工具执行器调用的方法。"""

    def __init__(self, todo_store: TodoStore) -> None:
        self.todo_store = todo_store

    def add_todo(self, task: str) -> dict[str, object]:
        """新增一条待办事项。"""

        return self.todo_store.add_todo(task=task)

    def list_todos(self) -> dict[str, list[dict[str, object]]]:
        """读取所有未完成待办，并包装成统一返回结构。"""

        return {"items": self.todo_store.list_open_todos()}
