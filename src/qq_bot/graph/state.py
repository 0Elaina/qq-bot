from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """图节点共享的状态；当前只保存按时间顺序排列的消息"""
    
    # 节点返回新消息时追加而非覆盖，ToolNode 才能读取模型的调用请求
    messages: Annotated[list[AnyMessage], add_messages]
