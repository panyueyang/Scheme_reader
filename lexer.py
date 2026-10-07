"""词法分析器：把程序文本切分成 token 列表。

token 类型：
    LPAREN   '('
    RPAREN   ')'
    QUOTE    "'"
    BOOL     '#t' / '#f'
    NUMBER   整数或浮点数
    STRING   带引号的字符串（已处理转义）
    SYMBOL   其他符号（变量名、操作符等）
"""

from dataclasses import dataclass
from typing import List, Any


@dataclass
class Token:
    type: str
    value: Any


class LexerError(Exception):
    """词法分析阶段抛出的错误。"""


def _is_delimiter(ch: str) -> bool:
    """判断字符是否是 token 之间的分隔符。"""
    return ch in ' \t\n\r()' or ch == ';'


def tokenize(source: str) -> List[Token]:
    """把源代码文本转换成 token 列表。

    Args:
        source: mini-Scheme 源代码文本。

    Returns:
        Token 对象列表。

    Raises:
        LexerError: 遇到非法字符或未闭合的字符串。
    """
    tokens: List[Token] = []
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]

        # 空白和注释：跳过
        if ch in ' \t\n\r':
            i += 1
            continue
        if ch == ';':
            while i < n and source[i] != '\n':
                i += 1
            continue

        # 括号
        if ch == '(':
            tokens.append(Token('LPAREN', '('))
            i += 1
            continue
        if ch == ')':
            tokens.append(Token('RPAREN', ')'))
            i += 1
            continue

        # quote 简写
        if ch == "'":
            tokens.append(Token('QUOTE', "'"))
            i += 1
            continue

        # 布尔
        if ch == '#' and i + 1 < n:
            if source[i + 1] == 't':
                tokens.append(Token('BOOL', True))
                i += 2
                continue
            if source[i + 1] == 'f':
                tokens.append(Token('BOOL', False))
                i += 2
                continue

        # 字符串（带引号）
        if ch == '"':
            i += 1
            start = i
            buf = []
            while i < n and source[i] != '"':
                if source[i] == '\\' and i + 1 < n:
                    nxt = source[i + 1]
                    if nxt == 'n':
                        buf.append('\n')
                    elif nxt == 't':
                        buf.append('\t')
                    elif nxt == '"':
                        buf.append('"')
                    elif nxt == '\\':
                        buf.append('\\')
                    else:
                        # 未知转义：原样保留反斜杠
                        buf.append('\\')
                        buf.append(nxt)
                    i += 2
                else:
                    buf.append(source[i])
                    i += 1
            if i >= n:
                raise LexerError("未闭合的字符串字面量")
            i += 1  # 跳过结束引号
            tokens.append(Token('STRING', ''.join(buf)))
            continue

        # 数字（整数或浮点数，可能带负号）
        if ch.isdigit() or (ch == '-' and i + 1 < n and source[i + 1].isdigit()):
            start = i
            if ch == '-':
                i += 1
            has_dot = False
            while i < n:
                c = source[i]
                if c.isdigit():
                    i += 1
                elif c == '.' and not has_dot:
                    has_dot = True
                    i += 1
                else:
                    break
            text = source[start:i]
            if has_dot:
                tokens.append(Token('NUMBER', float(text)))
            else:
                tokens.append(Token('NUMBER', int(text)))
            continue

        # 符号：读到下一个分隔符为止
        start = i
        while i < n and not _is_delimiter(source[i]):
            i += 1
        text = source[start:i]
        if not text:
            raise LexerError(f"无法识别的字符: {source[i]!r}")
        tokens.append(Token('SYMBOL', text))

    return tokens
