import asyncio

from qq_bot.domain.message import IncomingMessage
from qq_bot.graph.checkpoint import open_checkpointer
from qq_bot.graph.workflow import build_graph
from qq_bot.services.agent_service import reply_to_message


async def run_simulation() -> None:
    """运行真实大模型测试：覆盖闲聊、群聊过滤、Tool Calling 与跨轮记忆隔离"""
    print("=== 开始运行 QQ Bot 真实大模型验收测试 ===\n")

    # async with 确保 SQLite 异步连接在测试开始前完成 setup，在测试结束时无论成功失败均正确关闭
    async with open_checkpointer() as checkpointer:
        # 将 checkpointer 注入图，使节点每次流转都能持久化写入 SQLite
        graph = build_graph(checkpointer)

        test_messages = [
            # 场景 1：私聊闲聊（不触发工具）
            IncomingMessage(
                message_id=1,
                user_id=1001,
                text="你好！请问你能做什么？",
                chat_type="private",
            ),
            # 场景 2：群聊未 @（策略拦截，节省 Token）
            IncomingMessage(
                message_id=2,
                user_id=1001,
                text="帮我算一下 100 乘以 2",
                chat_type="group",
                group_id=2001,
                is_mentioned=False,
            ),
            # 场景 3：群聊 @ 触发自然语言应用题计算（Tool Calling 完整闭环）
            IncomingMessage(
                message_id=3,
                user_id=1001,
                text="我们部门有 24 人，买了 5 箱饮料每箱 12 瓶，平均每人分几瓶？",
                chat_type="group",
                group_id=2001,
                is_mentioned=True,
            ),
            # 场景 4：多轮记忆写入
            IncomingMessage(
                message_id=4,
                user_id=1001,
                text="请记住我的代号叫探戈狼",
                chat_type="private",
            ),
            # 场景 5：多轮记忆读取（验证同用户上下文延续）
            IncomingMessage(
                message_id=5,
                user_id=1001,
                text="还记得我的代号叫什么吗？",
                chat_type="private",
            ),
            # 场景 6：不同用户隐私隔离（验证 1002 读不到 1001 的记忆）
            IncomingMessage(
                message_id=6, user_id=1002, text="我的代号叫什么？", chat_type="private"
            ),
        ]

        for msg in test_messages:
            scene = f"[{msg.chat_type} user={msg.user_id} @={msg.is_mentioned}] '{msg.text}'"
            print(f">> 输入: {scene}")
            reply = await reply_to_message(graph, msg)
            print(f" -> 回复: {reply}\n")

def main() -> None:
    # 命令行同步入口，启动并托管异步事件循环
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
