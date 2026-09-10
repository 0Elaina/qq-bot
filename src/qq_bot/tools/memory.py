from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from qq_bot.repositories.memory_repo import memory_repo


@tool
async def record_user_memory(
    category: str, content: str, config: RunnableConfig
) -> str:
    """
    持久化记录当前用户的长效画像与关键事实（如喜好、生活习惯、个人约束或约定等）。
    使用准则：
    1. 仅在对话中自然获知用户的核心个人特质或明确偏好时调用，避免记录与用户无关的琐碎对话；
    2. category 建议使用简短分类词，如“喜好”、“习惯”、“事实”、“约定”等；
    3. content 须提炼为客观、自包含的陈述句（如“不吃香菜”、“最喜欢的动漫是《CLANNAD》”）。
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "错误: 未能识别当前会话的用户身份，记录失败"
    memory_id = await memory_repo.add_memory(
        user_id=int(user_id), category=category, content=content
    )
    return f"已成功持久化记录该事实（条目 ID: {memory_id})"


@tool
async def forget_user_memory(memory_id: int, config: RunnableConfig) -> str:
    """根据记忆条目 ID，废弃或删除某条过期/失效/已变更的历史事实。
    使用准则：
    1. 当用户明确表示某项事实不再成立（如“我不喜欢吃拉面了”），或要求遗忘某事时调用；
    2. 若用户更正了某项偏好，可先调用本工具废弃旧 ID 条目，再调用 record_user_memory 记录新事实；
    3. memory_id 必须是已知记忆列表中存在的数字 ID。
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "错误: 未能识别当前会话的用户身份，操作失败"

    success = await memory_repo.delete_memory(user_id=int(user_id), memory_id=memory_id)
    if success:
        return f"已成功废弃并删除 ID 为 {memory_id} 的记忆条目"
    return f"未能找到 ID 为 {memory_id} 的有效记忆 (可能已删除或不存在)"
