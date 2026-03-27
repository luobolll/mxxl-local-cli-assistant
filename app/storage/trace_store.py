"""trace 存储层。"""

from __future__ import annotations

from app.schemas.models import TraceRecord
from app.storage.sqlite import SQLiteManager


class TraceStore:
    """负责把每轮请求的 trace 写入数据库。"""

    def __init__(self, sqlite_manager: SQLiteManager) -> None:
        self.sqlite_manager = sqlite_manager

    def add_trace(self, trace_record: TraceRecord) -> None:
        """保存一条 trace 记录。"""

        with self.sqlite_manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO traces (
                    session_id,
                    user_input,
                    prompt_text,
                    model_output,
                    action_type,
                    tool_name,
                    tool_args_json,
                    tool_result_json,
                    final_response,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_record.session_id,
                    trace_record.user_input,
                    trace_record.prompt_text,
                    trace_record.model_output,
                    trace_record.action_type,
                    trace_record.tool_name,
                    trace_record.tool_args_json,
                    trace_record.tool_result_json,
                    trace_record.final_response,
                    trace_record.created_at,
                ),
            )
