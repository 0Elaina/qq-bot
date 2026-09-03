from functools import lru_cache
from pathlib import Path

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from qq_bot.config import config
from qq_bot.graph.state import AgentState
from qq_bot.tools.calculator import calculate


def get_model_with_tools():
    """初始化 OpenAI 兼容大模型客户端，并绑定计算器工具 Schema"""
    # 实例化客户端，通过 config 传入 Base URL 与 API Key
    model = ChatOpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
        model=config.openai_model_name,
        temperature=0.7,
    )
    # bind_tools 将 Python 函数签名与 docstring 转换为 API 认识的工具规范
    return model.bind_tools([calculate])


async def model_node(state: AgentState) -> dict[str, list[AIMessage]]:
    """LangGraph 模型节点：读取会话状态，动态注入人设并请求大模型"""
    model = get_model_with_tools()
    system_message = SystemMessage(content=load_persona_prompt())
    # 仅在请求模型时临时在头部拼接 SystemMessage，不污染 SQLite 会话历史
    message = [system_message, *state["messages"]]
    # ainvoke 异步非阻塞调用，支持高并发事件循环
    response = await model.ainvoke(message)
    # 仅返回增量消息，由 State 的 add_messages 自动追加
    return {"messages": [response]}


@lru_cache(maxsize=1)
def load_persona_prompt() -> str:
    """读取并缓存系统人设提示词"""
    project_root = Path(__file__).resolve().parents[3]
    prompt_file = project_root / "prompts" / "persona.md"
    return prompt_file.read_text(encoding="utf-8")
