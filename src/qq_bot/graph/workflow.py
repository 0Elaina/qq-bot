from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from qq_bot.graph.model import model_node
from qq_bot.graph.router import route_after_model
from qq_bot.graph.state import AgentState
from qq_bot.tools.anime import recommend_anime
from qq_bot.tools.calculator import execute_python

from langgraph.checkpoint.base import BaseCheckpointSaver

from qq_bot.tools.memory import forget_user_memory, record_user_memory
from qq_bot.tools.time import get_current_time


def build_graph(checkpointer: BaseCheckpointSaver):
    """构建 Agent 工作流：真实大模型自主决策，工具结果闭环返回模型"""

    workflow = StateGraph(AgentState)

    # 接入真实的 OpenAI 兼容模型节点，取代原有的 fake_model_node
    workflow.add_node("model", model_node)

    # ToolNode 负责按 tool_calls 调用白名单工具，业务代码不手动分派函数
    workflow.add_node(
        "tools",
        ToolNode(
            [
                execute_python,
                recommend_anime,
                get_current_time,
                record_user_memory,
                forget_user_memory,
            ]
        ),
    )

    # 每次图调用必须先由模型决定是直接回复，还是请求调用工具
    workflow.add_edge(START, "model")

    # 条件路由：检查模型是否发出了 tool_calls，若有转入 tools，若无转入 END
    workflow.add_conditional_edges(
        "model", route_after_model, {"tools": "tools", "end": END}
    )

    # 工具结果必须回到模型，才能形成用户可读的最终 AIMessage
    workflow.add_edge("tools", "model")

    # checkpointer 按调用方传入的 thread_id 保存 State，图本身不依赖 SQLite 表结构
    return workflow.compile(checkpointer=checkpointer)
