from datetime import datetime

from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """获取当前现实世界的系统日期与时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
