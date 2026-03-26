"""SQLite 连接和表结构初始化。

这个模块只负责数据库连接和建表，不负责具体业务查询。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY,
        task TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY,
        key TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS traces (
        id INTEGER PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_input TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        model_output TEXT NOT NULL,
        action_type TEXT NOT NULL,
        tool_name TEXT,
        tool_args_json TEXT,
        tool_result_json TEXT,
        final_response TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
]


class SQLiteManager:
    """统一管理 SQLite 数据库连接。"""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        """初始化数据库文件和表结构。"""

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)

    def connect(self) -> sqlite3.Connection:
        """创建一个新的数据库连接。

        row_factory 设置为 sqlite3.Row 后，查询结果可以按列名访问，
        代码可读性会比使用索引更好。
        """

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        # 当前工作区所在盘符对 SQLite 默认文件 journal 支持不稳定，
        # 这里显式切到 MEMORY 模式，避免写入时出现 disk I/O error。
        connection.execute("PRAGMA journal_mode=MEMORY")
        return connection
