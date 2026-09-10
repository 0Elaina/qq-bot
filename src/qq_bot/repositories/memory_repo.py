from pathlib import Path

import aiosqlite

DEFAULT_PATH = Path("data/bot.db")


class MemoryRepository:
    """基于 aiosqlite 的长效记忆异步持久化仓储"""

    def __init__(self, db_path: Path = DEFAULT_PATH):
        self.db_path = db_path

    async def init_db(self) -> None:
        """初始化数据库目录、表结构与查询索引"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_user ON user_memories(user_id)"
            )
            await db.commit()

    async def add_memory(self, user_id: int, category: str, content: str) -> int:
        """为指定用户新增一条长效记忆事实，返回生成的主键 ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO user_memories (user_id, category, content) VALUES (?, ?, ?)",
                (user_id, category.strip(), content.strip()),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def delete_memory(self, user_id: int, memory_id: int) -> bool:
        """根据 ID 废弃记忆条目，防御性绑定 user_id 杜绝越权删除"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM user_memories WHERE id = ? AND user_id = ?",
                (memory_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_active_memories(self, user_id: int, limit: int = 30) -> list[dict]:
        """获取指定用户的活跃长效记忆条目（按最近创建倒序，限制条数）"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, category, content, created_at
                FROM user_memories
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


# 导出仓储单例，供工具与图节点统一调用
memory_repo = MemoryRepository()
