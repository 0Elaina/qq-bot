import asyncio

from qq_bot.domain.message import IncomingMessage
from qq_bot.graph.checkpoint import open_checkpointer
from qq_bot.graph.workflow import build_graph
from qq_bot.services.agent_service import reply_to_message


async def run_simulation() -> None:
    """运行多场景离线模拟：验证私聊、群聊 @、计算器工具与状态隔离"""
    print("=== 开始运行 QQ Bot 离线模拟测试 ===")

    # async with 确保 SQLite 异步连接在测试开始前完成 setup，在测试结束时无论成功失败均正确关闭
    async with open_checkpointer() as checkpointer:
        # 将 checkpointer 注入图，使节点每次流转都能持久化写入 SQLite
        graph = build_graph(checkpointer)

        # 覆盖 5 个关键验收场景：私聊、未 @ 群聊、@ 群聊、恶意代码拦截、不同用户隔离
        test_messages = [
            IncomingMessage(
                message_id=1, user_id=1001, text="计算 2 * (3 + 4)", chat_type="private"
            ),
            IncomingMessage(
                message_id=2,
                user_id=1001,
                text="计算 1 + 1",
                chat_type="group",
                group_id=2001,
                is_mentioned=False,
            ),
            IncomingMessage(
                message_id=3,
                user_id=1001,
                text="计算 (10 - 2) / 4",
                chat_type="group",
                group_id=2001,
                is_mentioned=True,
            ),
            IncomingMessage(
                message_id=4,
                user_id=1001,
                text="计算 __import__('os').system('dir')",
                chat_type="private",
            ),
            IncomingMessage(
                message_id=5,
                user_id=1002,
                text="计算 5 + 5",
                chat_type="group",
                group_id=2001,
                is_mentioned=True,
            ),
        ]

        for msg in test_messages:
            # 异步执行每条消息，提取回复文本（若被策略忽略则返回 None）
            reply = await reply_to_message(graph, msg)
            scene = f"[{msg.chat_type} user={msg.user_id} @={msg.is_mentioned}] '{msg.text}'"
            print(f"{scene}\n -> 回复: {reply}")


def main() -> None:
    # 命令行同步入口，启动并托管异步事件循环
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
