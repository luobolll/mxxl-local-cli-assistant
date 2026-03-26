"""管理当前命令行会话。"""

from __future__ import annotations

import uuid


class SessionManager:
    """负责生成和切换当前活动会话 ID。"""

    def __init__(self) -> None:
        self._current_session_id = self._new_session_id()

    def get_current_session_id(self) -> str:
        """返回当前活动会话 ID。"""

        return self._current_session_id

    def reset_session(self) -> str:
        """创建一个新的会话 ID，并把它设为当前会话。"""

        self._current_session_id = self._new_session_id()
        return self._current_session_id

    def _new_session_id(self) -> str:
        """生成新的唯一会话 ID。"""

        return f"session-{uuid.uuid4().hex}"
