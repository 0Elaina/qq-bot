from qq_bot.domain.message import IncomingMessage


def build_thread_id(message: IncomingMessage) -> str:
    """生成可用于 LangGraph 状态隔离的会话编号"""
    
    if message.chat_type == "private":
        return f"private:{message.user_id}"
    
    if message.group_id is None:
        raise ValueError("群聊消息必须提供 group_id")
    
    # 群内按“群 + 用户”隔离，避免不同群或不同用户共享聊天历史
    return f"group:{message.group_id}:user:{message.user_id}"