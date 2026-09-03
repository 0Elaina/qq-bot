from typing import Literal

from langchain_core.messages import AIMessage

from qq_bot.graph.state import AgentState


def route_after_model(state: AgentState) -> Literal["tools", "end"]:
    """根据模型最新消息决定进入 ToolNode 或结束图运行"""
    last_message = state["messages"][-1]

    # 只接受模型明确提出的工具调用，普通文本回复直接作为最终结果
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "end"
