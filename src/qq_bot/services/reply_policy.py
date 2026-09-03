from qq_bot.domain.message import IncomingMessage


def should_reply(message: IncomingMessage) -> bool:
    """根据聊天场景决定消息是否可进入 Agent 工作流"""
    # 空白消息不送入模型，避免无意义调用和后续平台格式差异
    if not message.text.strip():
        return False
    
    if message.chat_type == "private":
        return True
    
    # 群聊必须显式 @，机器人不会主动参与普通群消息
    return message.is_mentioned