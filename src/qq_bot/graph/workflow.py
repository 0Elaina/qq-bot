from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from qq_bot.graph.fake_model import fake_model_node
from qq_bot.graph.router import route_after_model
from qq_bot.graph.state import AgentState
from qq_bot.tools.calculator import calculate

from langgraph.checkpoint.base import BaseCheckpointSaver


def build_graph(checkpointer: BaseCheckpointSaver):
    """构建离线 Agent：模型可调用计算器，工具结果再返回模型"""

    workflow = StateGraph(AgentState)

    # 模型节点既处理用户输入，也读取 ToolNode 写回 State 的工具结果
    workflow.add_node("model", fake_model_node)

    # ToolNode 负责按 tool_calls 调用白名单工具，业务代码不手动分派函数
    workflow.add_node("tools", ToolNode([calculate]))

    # 每次图调用必须先由模型决定是直接回复，还是请求调用工具
    workflow.add_edge(START, "model")

    # Router 的返回值映射到节点名或 END，避免把普通文本误送进 ToolNode
    workflow.add_conditional_edges(
        "model", route_after_model, {"tools": "tools", "end": END}
    )

    # 工具结果必须回到模型，才能形成用户可读的最终 AIMessage
    workflow.add_edge("tools", "model")

    # checkpointer 按调用方传入的 thread_id 保存 State，图本身不依赖 SQLite 表结构
    return workflow.compile(checkpointer=checkpointer)
