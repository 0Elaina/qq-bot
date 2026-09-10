from functools import lru_cache
from pathlib import Path

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from qq_bot.config import config
from qq_bot.graph.state import AgentState
from qq_bot.repositories.memory_repo import memory_repo
from qq_bot.tools.anime import recommend_anime
from qq_bot.tools.calculator import execute_python
from qq_bot.tools.memory import forget_user_memory, record_user_memory
from qq_bot.tools.time import get_current_time
from qq_bot.tools.voice import send_voice_message


def get_model_with_tools():
    """初始化 OpenAI 兼容大模型客户端，并绑定可用工具 Schema"""
    # 实例化客户端，通过 config 传入 Base URL 与 API Key
    model = ChatOpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
        model=config.openai_model_name,
        temperature=0.7,
    )
    # bind_tools 将 Python 函数签名与 docstring 转换为 API 认识的工具规范
    return model.bind_tools(
        [
            execute_python,
            recommend_anime,
            get_current_time,
            record_user_memory,
            forget_user_memory,
            send_voice_message
        ]
    )


async def _build_memory_context(user_id: int | None) -> str:
    """根据当前用户 ID 查询活跃长效记忆，格式化为带条目 ID 的注入清单"""
    if not user_id:
        return ""
    memories = await memory_repo.get_active_memories(user_id=user_id)
    if not memories:
        return ""
    lines = [f"- [ID: {m['id']}] [{m['category']}] [{m['content']}]" for m in memories]
    return "\n\n## 关于当前用户的已知长效记忆与事实 (仅供参考): \n" + "\n".join(lines)


async def model_node(
    state: AgentState, config: RunnableConfig
) -> dict[str, list[AIMessage]]:
    """LangGraph 模型节点：读取会话状态，动态注入人设并请求大模型"""
    model = get_model_with_tools()
    user_id = config.get("configurable", {}).get("user_id")
    memory_context = await _build_memory_context(int(user_id) if user_id else None)

    # 动态组装：基础人设 + 该用户的长效记忆（纯内存无状态拼接，不污染数据库历史）
    full_prompt = load_persona_prompt() + memory_context
    system_message = SystemMessage(content=full_prompt)

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
