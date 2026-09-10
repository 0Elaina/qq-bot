from langchain_core.messages import HumanMessage

from qq_bot.domain.message import IncomingMessage
from langgraph.graph.state import CompiledStateGraph

from qq_bot.services.reply_policy import should_reply
from qq_bot.services.session import build_thread_id


async def reply_to_message(
    graph: CompiledStateGraph, message: IncomingMessage
) -> str | None:
    """对一条标准化消息生成回复；不应回复时返回 None"""

    # 忽略的消息不进入图，也不会创建无意义的 SQLite 会话状态
    if not should_reply(message):
        return None

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=message.text)]},
        {
            "configurable": {
                "thread_id": build_thread_id(message),
                "user_id": message.user_id,
                "chat_type": message.chat_type,
                "group_id": message.group_id
            }
        },
    )

    return str(result["messages"][-1].content)
