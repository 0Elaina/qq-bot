import asyncio

from langgraph.graph.state import CompiledStateGraph

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from httpx import AsyncClient
import uvicorn

from qq_bot.adapters.onebot import parse_onebot_event, send_onebot_reply
from qq_bot.config import config
from qq_bot.domain.message import IncomingMessage
from qq_bot.graph.checkpoint import open_checkpointer
from qq_bot.graph.workflow import build_graph
from qq_bot.repositories.memory_repo import memory_repo
from qq_bot.services.agent_service import reply_to_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理器，统一托管异步数据库连接池与 HTTP 客户端
    Args:
        app: FastAPI 应用实例，用于将全局持久化对象挂载至 app.state
    """
    # 启动阶段：建立 SQLite 异步检查点连接与持久化 HTTP 客户端
    await memory_repo.init_db()
    async with open_checkpointer() as checkpointer:
        async with AsyncClient(
            base_url=config.napcat_http_url, timeout=30.0
        ) as http_client:
            app.state.graph = build_graph(checkpointer)
            app.state.http_client = http_client
            print(
                f"[Server] 服务已启动, 监听 {config.server_host}:{config.server_port}"
            )
            yield
    # 关闭阶段：退出上下文时自动安全释放数据库与网络资源
    print("[Server] 服务已安全关闭, 资源已释放")


app = FastAPI(title="QQ LangGraph Bot", lifespan=lifespan)


async def dispatch_message(
    graph: CompiledStateGraph, client: AsyncClient, message: IncomingMessage
) -> None:
    """
    异步并发工作协程：调用 LangGraph 图推理，并将回复推回 QQ 客户端
    Args:
        graph: 编译后的 LangGraph 工作流图实例
        client: 共享的 httpx 异步客户端
        message: 解析后的标准化 IncomingMessage 领域消息
    """
    try:
        reply = await reply_to_message(graph, message)
        # 仅在策略允许回复且生成了有效内容时发送，被忽略的消息（reply is None）静默跳过
        if reply:
            await send_onebot_reply(client, message, reply)
    except Exception as e:
        # 异常边界：捕获并打印局部异常，防止后台任务静默失败或影响事件循环
        print(f"[Error] 处理消息失败 message_id={message.message_id}: {e}")


@app.websocket("/onebot/v11/ws")
async def onebot_websocket_endpoint(websocket: WebSocket) -> None:
    """
    NapCat 反向 WebSocket 端点，持续监听事件并通过后台任务非阻塞并发派发
    Args:
        websocket: FastAPI 注入的 WebSocket 长连接实例
    """
    await websocket.accept()
    print("[OneBot] NapCat 反向 WebSocket 客户端已成功连接")
    try:
        while True:
            data = await websocket.receive_json()
            incoming_msg = parse_onebot_event(data, config.bot_qq)
            if incoming_msg:
                # 核心机制：以非阻塞后台 Task 执行，确保接收循环零等待监听下一个事件
                asyncio.create_task(
                    dispatch_message(
                        app.state.graph, app.state.http_client, incoming_msg
                    )
                )
    except WebSocketDisconnect:
        print("[OneBot] NapCat 反向 WebSocket 连接已断开")


def main() -> None:
    """服务启动入口函数，托管 uvicorn ASGI 服务器运行"""
    uvicorn.run(
        "qq_bot.server:app",
        host=config.server_host,
        port=config.server_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
