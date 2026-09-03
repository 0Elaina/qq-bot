import ast
import operator

from langchain_core.tools import tool

# 只有字典中的 AST 运算节点能执行，函数调用等其他节点一律拒绝
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def evaluate_expression(expression: str) -> int | float:
    """安全计算由数字、括号和四则运算符组成的表达式"""
    try:
        root = ast.parse(expression, mode="eval").body
    except SyntaxError as error:
        raise ValueError("表达式语法错误") from error
    return _evaluate(root)


def _evaluate(node: ast.expr) -> int | float:
    """递归计算一个 AST 节点；只接受预先允许的节点类型"""

    # 递归终点：节点本身就是数字，例如表达式里的 7 或 3.5
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    # 递归步骤：二元运算节点包含 left、op、right，例如 7 + 5
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left_value = _evaluate(node.left)
        right_value = _evaluate(node.right)

        # 两侧都先被算成数字后，才执行已经列入白名单的运算符
        operation = _OPERATORS[type(node.op)]
        return operation(left_value, right_value)
    # 未列入白名单的节点（函数、变量、幂运算等）不能执行
    raise ValueError("只允许数字、括号和 + - * /")


@tool
def calculate(expression: str) -> str:
    """计算安全的四则运算表达式，例如 '(7 + 5) * 3'"""
    try:
        result = evaluate_expression(expression)
    except ZeroDivisionError:
        # ToolNode 需要获得正常结果，不能让一个除零错误中断整个 Agent
        return "计算失败: 除数不能为 0"
    except ValueError as error:
        return f"计算失败: {error}"

    return f"计算结果: {result}"
