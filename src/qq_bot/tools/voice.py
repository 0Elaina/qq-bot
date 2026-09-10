import base64

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from qq_bot.config import config

FISH_AUDIO_TTS_URL = "https://api.fish.audio/v1/tts"


async def _synthesize_fish_audio(text: str) -> bytes | None:
    """
    调用 Fish Audio 开放接口合成 MP3 二进制音频数据。
    采用“付费优先 -> 402自动降级免费 -> 失败降级文本”的三级容错架构。
    """
    # 守门检查：未配置 Key 时快速降级，避免产生无效的网络请求与报错
    if not config.fish_audio_api_key:
        return None

    # 构造 Bearer 认证头与标准 JSON 请求头
    headers = {
        "Authorization": f"Bearer {config.fish_audio_api_key}",
        "Content-Type": "application/json",
    }

    # reference_id 绑定声线，format 指定输出轻量通用的 MP3 格式
    payload = {
        "text": text,
        "reference_id": config.fish_audio_voice_id,
        "format": "mp3",
    }

    # 采用异步 HTTP 客户端发起非阻塞 POST 请求，连接池自动安全回收
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 第一阶：优先请求付费生产通道
        response = await client.post(FISH_AUDIO_TTS_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.content

        # 第二阶：若命中 HTTP 402（账户无付费额度），自动平滑降级到免费开发模型
        if response.status_code == 402:
            print("[FishAudio] 付费额度不足(HTTP 402)，自动平滑降级至免费开发模型 (s2.1-pro-free)...")
            free_headers = {**headers, "model": "s2.1-pro-free"}
            free_resp = await client.post(FISH_AUDIO_TTS_URL, json=payload, headers=free_headers)
            if free_resp.status_code == 200:
                return free_resp.content
            print(f"[FishAudio] 免费模型请求失败 HTTP {free_resp.status_code}: {free_resp.text}")
            return None

        # 其他异常状态码（如 401 密钥错误或 500 服务器错误）
        print(f"[FishAudio] 合成失败 HTTP {response.status_code}: {response.text}")
        return None


async def _send_record_to_napcat(b64_audio: str, configurable: dict) -> bool:
    """将 Base64 编码的音频作为 OneBot 11 语音条异步推送到 NapCat 网关"""
    chat_type = configurable.get("chat_type", "private")
    user_id = configurable.get("user_id")
    group_id = configurable.get("group_id")

    # 封装 OneBot 11 标准语音 CQ 码
    cq_record = f"[CQ:record,file=base64://{b64_audio}]"

    # 根据当前触发场景，将语音路由到对应会话窗口
    if chat_type == "group" and group_id:
        endpoint = f"{config.napcat_http_url}/send_group_msg"
        payload = {"group_id": group_id, "message": cq_record}
    else:
        endpoint = f"{config.napcat_http_url}/send_private_msg"
        payload = {"user_id": user_id, "message": cq_record}

    # 异步非阻塞推送到 NapCat HTTP 服务
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            return response.status_code == 200
    except Exception as e:
        print(f"[NapCat] 语音消息推送跳过 (连接未建立或处于离线测试模式): {e}")
        return False


@tool
async def send_voice_message(text: str, config: RunnableConfig) -> str:
    """
    合成并向当前 QQ 会话发送一条语音条消息。
    使用准则：
    1. 仅在用户明确要求发送语音，或对话情境适宜且需要语音表达时调用；
    2. 入参 text 必须为日文文本（如简短问候、情感短句）；
    3. 本工具仅负责音频合成与发送。调用成功后，必须在随后的最终文本回复中，以完全相同的中文语义进行表达与回应。
    """
    # 从上下文信封中获取当前会话路由元数据
    configurable = config.get("configurable", {})
    
    # 调用 Fish Audio 异步合成 MP3 原始字节流
    audio_bytes = await _synthesize_fish_audio(text.strip())
    # 防御兜底：API 未配或异常时，引导模型优雅降级为纯文本回复
    if not audio_bytes:
        return "系统提示: 语音合成不可用或生成失败，请直接使用对应语义的中文文本回复用户。"
    
    # 纯内存 Base64 编码，不经过任何磁盘读写
    b64_str = base64.b64encode(audio_bytes).decode("utf-8")

    # 推送到 NapCat 对应的会话窗口（私聊或群聊）
    sent = await _send_record_to_napcat(b64_audio=b64_str, configurable=configurable)
    status_desc = "已成功投递到 QQ" if sent else "已在内存中合成完毕(离线模式)"
    
    # 返回客观中立的执行状态与双语对齐提示
    return f"语音条{status_desc}。请务必在随后的文本回复中，使用完全相同的中文语义回复用户。"