"""打印模块：把内部表示的值转成 mini-Scheme 的表面语法。

值在内部的表示约定：
    - 整数 / 浮点 / 布尔 → 原样
    - 字符串 → ('string', "内容")
    - 符号 → Python str
    - 点对 → ('pair', car, cdr)
    - 空表 → ('nil',)
    - 内置过程 → ('builtin', name, fn)
    - 用户过程 → ('closure', params, body, env)
"""

from typing import Any


def _escape_string(s: str) -> str:
    """把字符串内容转成带转义的表面形式。"""
    return (s.replace('\\', '\\\\')
             .replace('"', '\\"')
             .replace('\n', '\\n')
             .replace('\t', '\\t'))


def _is_pair(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 3 and v[0] == 'pair'


def _is_nil(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 1 and v[0] == 'nil'


def _is_string(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 2 and v[0] == 'string'


def _is_closure(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 4 and v[0] == 'closure'


def _is_builtin(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 3 and v[0] == 'builtin'


def to_string(v: Any) -> str:
    """把值转成顶层打印用的字符串。"""
    if v is True:
        return '#t'
    if v is False:
        return '#f'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    if _is_string(v):
        return f'"{_escape_string(v[1])}"'
    if isinstance(v, str):
        return v
    if _is_nil(v):
        return '()'
    if _is_pair(v):
        return _pair_to_string(v)
    if _is_closure(v) or _is_builtin(v):
        return '#<procedure>'
    return str(v)


def _pair_to_string(pair) -> str:
    """把点对链转成列表/点对字符串。"""
    parts = []
    cur = pair
    while _is_pair(cur):
        parts.append(to_string(cur[1]))
        cur = cur[2]
    if _is_nil(cur):
        return f"({' '.join(parts)})"
    # 非法点对，用 . 表示
    return f"({' '.join(parts)} . {to_string(cur)})"


def display_to_string(v: Any) -> str:
    """display 用的字符串：字符串不带引号。"""
    if _is_string(v):
        return v[1]
    return to_string(v)
