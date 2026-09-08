from contextlib import redirect_stdout
from datetime import datetime
import io
import math
import random

from langchain_core.tools import tool

# 受限安全环境：不注入 __import__，天然阻断未授权模块动态加载
_SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "sorted": sorted,
    "enumerate": enumerate,
    "zip": zip,
}


def _get_safe_globals() -> dict:
    """构建隔离的执行命名空间，安全注入白名单模块与内置函数"""
    return {
        "__builtins__": _SAFE_BUILTINS,
        "math": math,
        "random": random,
        "datetime": datetime,
    }


@tool
def execute_python(code: str) -> str:
    """在安全的 Python 沙箱中执行代码或数学表达式，返回运算或打印结果。

    使用指南：
    1. 大模型可通过编写标准 Python 代码完成任意高精度计算、数学公式、几何/复利算法、概率统计或复杂逻辑；
    2. 支持单行表达式直接求值（如 '2**10'、'math.sqrt(144)'）；
    3. 多行脚本请使用 print(...) 打印最终输出结果；
    4. 沙箱内预置了 math、random、datetime 模块及常用内置函数。
    """
    cleaned_code = code.strip()
    if not cleaned_code:
        return "错误: 代码内容为空"

    safe_globals = _get_safe_globals()

    # 模式 1：优先尝试作为单行表达式直接求值（针对 '2**10', '15.5 * 3' 等无 print 场景）
    try:
        eval_result = eval(cleaned_code, safe_globals)
        if eval_result is not None:
            return f"计算结果: {eval_result}"
    except SyntaxError:
        # 存在多行语句、循环或赋值时，转入模式 2 执行
        pass
    except Exception as error:
        return f"计算失败: {type(error).__name__}: {error}"

    # 模式 2：执行脚本代码块并捕获 stdout 标准输出
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(cleaned_code, safe_globals)
    except Exception as error:
        return f"代码执行出错: {type(error).__name__}: {error}"

    output = buffer.getvalue().strip()
    if not output:
        return "代码执行完成（无输出，建议使用 print(...) 输出结果）。"
    return output

