from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from qq_bot.graph.state import AgentState

CALCULATION_PREFIX = "计算"


def extract_expression(message: HumanMessage) -> str | None:
    """从模拟协议中提取计算表达式；非计算消息返回 None"""
    # 假模型只接受纯文本，避免把多媒体内容误当作可执行表达式
    if not isinstance(message.content, str):
        return None

    if not message.content.startswith(CALCULATION_PREFIX):
        return None

    expression = message.content.removeprefix(CALCULATION_PREFIX).strip()
    return expression or None


def create_calculation_request(expression) -> AIMessage:
    """创建供 ToolNode 识别的计算器调用请求"""

    # 格式为 calculate_<32 位随机十六进制串>，如 calculate_a1b2...
    call_id = f"calculate_{uuid4().hex}"

    # id 必须唯一；多次计算时 ToolMessage 才不会关联到错误的调用请求
    return AIMessage(
        content="",
        tool_calls=[
            {"name": "calculate", "args": {"expression": expression}, "id": call_id}
        ],
    )


def fake_model_node(state: AgentState) -> dict[str, list[AIMessage]]:
    """模拟模型：计算请求生成 tool_calls, 其他用户消息直接回复"""
    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        # ToolNode 已完成调用；这里必须返回普通 AIMessage，作为图的最终回复
        return {"messages": [AIMessage(content=f"计算器返回: {last_message.content}")]}

    if isinstance(last_message, HumanMessage):
        expression = extract_expression(last_message)
        if expression is not None:
            return {"messages": [create_calculation_request(expression)]}

    # 没有可计算表达式时，不发起工具调用，直接给出普通回复
    return {"messages": [AIMessage(content="请以 [计算 表达式] 的形式提问")]}
