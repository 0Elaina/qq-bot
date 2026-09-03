from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

CHECKPOINT_DB = Path("data/agent_state.db")


@asynccontextmanager
async def open_checkpointer() -> AsyncGenerator[AsyncSqliteSaver, None]:
    """创建 SQLite checkpointer，并确保其内部状态表已准备完成"""

    # 创建目录, 如果存在多级目录则递归创建, 如果已经存在不抛出异常
    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)

    # from_conn_string 创建异步 SQLite 连接；async with 负责无论成功或异常都关闭它
    async with AsyncSqliteSaver.from_conn_string(str(CHECKPOINT_DB)) as checkpointer:
        # LangGraph 自己的 checkpoint 表首次需要创建，重复调用也可安全执行
        await checkpointer.setup()

        # 把已就绪的资源暂借给调用方；退出调用方的 async with 后会回到上方关闭连接
        yield checkpointer
