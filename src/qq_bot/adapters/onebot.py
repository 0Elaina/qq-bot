from httpx import AsyncClient

from qq_bot.domain.message import IncomingMessage


def extract_text_and_mention(raw_message: object, bot_qq: int) -> tuple[str, bool]:
    """
    从 OneBot 原始消息对象中提取纯净文本，并识别是否明确 @ 了机器人
    Args:
        raw_message: OneBot 原始消息对象，包含 message_id、user_id、text、chat_type、group_id 等字段
        bot_qq: 机器人 QQ 号，用于判断是否被 @
    Returns:
        tuple: (纯净文本, 是否被 @)
    """
    text_parts: list[str] = []
    is_mentioned: bool = False

    # 处理标准 Array 格式（OneBot 11 官方推荐）
    if isinstance(raw_message, list):
        for seg in raw_message:
            seg_type = seg.get("type")
            # 统一转为 str 对比，消除 JSON 反序列化时 QQ 号为 int 或 str 的类型差异
            if seg_type == "at" and str(seg.get("data", {}).get("qq")) == str(bot_qq):
                is_mentioned = True
            elif seg_type == "text":
                text_parts.append(seg.get("data", {}).get("text", ""))

    # 处理 String 格式（兼顾老旧客户端推送的 CQ 码字符串）
    elif isinstance(raw_message, str):
        target_cq = f"[CQ:at,qq={bot_qq}]"
        if bot_qq and target_cq in raw_message:
            is_mentioned = True
            # 剥离 @ 标签，仅把后面的有效问题文本交付后续处理
            raw_message = raw_message.replace(target_cq, "")
        text_parts.append(raw_message)

    return "".join(text_parts).strip(), is_mentioned


def parse_onebot_event(data: dict, bot_qq: int) -> IncomingMessage | None:
    """
    解析 OneBot 11 事件，过滤非消息事件并转换为内部领域模型 IncomingMessage
    Args:
        data: OneBot 11 推送的原始事件字典，包含 post_type、message_type、user_id 等字段
        bot_qq: 机器人自身 QQ 号，用于防自言自语死循环与 @ 判定
    Returns:
        IncomingMessage | None: 校验通过返回领域消息对象，非消息或需忽略时返回 None
    """
    # 守门检查：忽略心跳包 (meta_event)、通知 (notice) 和加群请求 (request)
    if data.get("post_type") != "message":
        return None

    # 防死循环：忽略机器人自身发出的消息，避免左右互搏
    user_id = data.get("user_id", 0)
    if bot_qq and user_id == bot_qq:
        return None

    # 范围限定：只接收私聊与群聊文本消息
    chat_type = data.get("message_type")
    if chat_type not in ("private", "group"):
        return None

    # 提取纯净问题文本与 @ 状态
    clean_text, is_mentioned = extract_text_and_mention(data.get("message"), bot_qq)

    return IncomingMessage(
        message_id=data.get("message_id", 0),
        user_id=user_id,
        text=clean_text,
        chat_type=chat_type,
        group_id=data.get("group_id"),
        is_mentioned=is_mentioned,
    )


async def send_onebot_reply(
    client: AsyncClient, message: IncomingMessage, reply_text: str
) -> None:
    """
    向 NapCat HTTP API 异步发送回复消息，将结果投递回 QQ 客户端
    Args:
        client: 共享的 httpx 异步客户端实例，实现 HTTP 连接池复用
        message: 触发本次回复的原始领域消息，用于提供接收目标与聊天类型
        reply_text: 大模型或业务层生成的最终回复文本
    """
    # 根据聊天类型路由到对应的 OneBot 11 HTTP 接口
    if message.chat_type == "private":
        endpoint = "/send_private_msg"
        payload = {"user_id": message.user_id, "message": reply_text}
    else:
        endpoint = "/send_group_msg"
        payload = {"group_id": message.group_id, "message": reply_text}

    # 异步非阻塞 POST 请求，状态码异常时触发预警
    response = await client.post(endpoint, json=payload)
    response.raise_for_status()