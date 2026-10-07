"""语法分析器：把 token 列表解析成嵌套的表达式树。

mini-Scheme 的表达式用嵌套列表表示：
    - 数字、布尔、字符串、符号 → 叶子节点
    - 列表 → Python list
    - quote 简写 'x → ['quote', x]
"""

from typing import List, Any
from lexer import Token


class ParserError(Exception):
    """语法分析阶段抛出的错误。"""


def parse(tokens: List[Token]) -> List[Any]:
    """把 token 列表解析成多个顶层表达式。

    Args:
        tokens: 词法分析器产生的 Token 列表。

    Returns:
        顶层表达式列表。

    Raises:
        ParserError: 括号不匹配或出现意外的 token。
    """
    exprs = []
    i = 0
    n = len(tokens)
    while i < n:
        expr, i = _parse_expr(tokens, i)
        exprs.append(expr)
    return exprs


def _parse_expr(tokens: List[Token], i: int) -> (Any, int):
    """解析单个表达式，返回 (表达式, 下一个下标)。"""
    token = tokens[i]

    if token.type == 'LPAREN':
        return _parse_list(tokens, i + 1)
    if token.type == 'RPAREN':
        raise ParserError("意外的右括号 ')'")
    if token.type == 'QUOTE':
        sub, j = _parse_expr(tokens, i + 1)
        return ['quote', sub], j

    # 原子值
    if token.type == 'BOOL':
        return token.value, i + 1
    if token.type == 'NUMBER':
        return token.value, i + 1
    if token.type == 'STRING':
        return ('string', token.value), i + 1
    if token.type == 'SYMBOL':
        return token.value, i + 1

    raise ParserError(f"无法识别的 token: {token}")


def _parse_list(tokens: List[Token], i: int) -> (List[Any], int):
    """解析括号内的列表，返回 (列表, 下一个下标)。"""
    result = []
    n = len(tokens)
    while i < n:
        token = tokens[i]
        if token.type == 'RPAREN':
            return result, i + 1
        expr, i = _parse_expr(tokens, i)
        result.append(expr)
    raise ParserError("未闭合的左括号 '('")
