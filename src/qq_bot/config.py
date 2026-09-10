from dataclasses import dataclass
import os

from dotenv import load_dotenv

# 加载当前目录下的 .env 文件到系统环境变量中
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """全局只读应用配置，集中管理模型连接参数与凭证"""

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    openai_model_name: str = os.getenv("OPENAI_MODEL_NAME", "deepseek-v4-flash")

    # NapCat 通信配置
    napcat_http_url: str = os.getenv("NAPCAT_HTTP_URL", "http://localhost:3000")
    bot_qq: int = int(os.getenv("BOT_QQ", "0"))
    server_host: str = os.getenv("SERVER_HOST", "127.0.0.1")
    server_port: int = int(os.getenv("SERVER_PORT", "8080"))
    
    # Fish Audio 二次元语音合成配置
    fish_audio_api_key: str = os.getenv("FISH_AUDIO_API_KEY", "")
    fish_audio_voice_id: str = os.getenv("FISH_AUDIO_VOICE_ID", "7f92f8afb8ec43bf81429cc1c9199cb1")
    


# 导出单例配置对象，全项目统一引用
config = AppConfig()
