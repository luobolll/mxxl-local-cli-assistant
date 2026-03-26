"""trace 记录器。

这个模块负责把一次请求的完整轨迹写入存储，并同步输出日志。
"""

from __future__ import annotations

import logging

from app.schemas.models import TraceRecord
from app.storage.trace_store import TraceStore


class TraceLogger:
    """负责记录正常 trace 和异常 trace。"""

    def __init__(self, trace_store: TraceStore) -> None:
        self.trace_store = trace_store
        self.logger = logging.getLogger("assistant.trace")
        if not self.logger.handlers:
            # 只在没有处理器时初始化 logging，避免重复配置日志系统。
            logging.basicConfig(level=logging.INFO)

    def record(self, trace_record: TraceRecord) -> None:
        """记录一次正常执行的 trace。"""

        self.trace_store.add_trace(trace_record)
        self.logger.info(
            "已记录请求轨迹 session_id=%s action_type=%s",
            trace_record.session_id,
            trace_record.action_type,
        )

    def record_error(self, trace_record: TraceRecord, exc: Exception) -> None:
        """记录一次带异常的 trace。"""

        self.trace_store.add_trace(trace_record)
        self.logger.exception(
            "请求处理失败，已记录 trace session_id=%s error=%s",
            trace_record.session_id,
            exc,
        )
