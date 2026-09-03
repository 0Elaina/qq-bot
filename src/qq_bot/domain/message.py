from dataclasses import dataclass
from typing import Literal

# 限定聊天类型为私聊或群聊
ChatType = Literal["private", "group"]


@dataclass(frozen=True, slots=True)
class IncomingMessage:
    """消息适配层的标准输出，供 Service 层进行回复与会话判断"""

    message_id: int
    user_id: int
    text: str
    chat_type: ChatType
    group_id: int | None = None
    
    # @ 判断只做一次，避免业务层依赖 QQ 原始消息格式
    is_mentioned: bool = False
