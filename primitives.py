"""内置过程库：把 mini-Scheme 的全部内置函数放进初始环境。

内置过程在求值器中的表示：('builtin', name, python_fn)
python_fn 接收一个 Python list（已求值的参数），返回一个值。
"""

from typing import Any, List
from printer import display_to_string, to_string


def _is_pair(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 3 and v[0] == 'pair'


def _is_nil(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 1 and v[0] == 'nil'


def _is_string(v: Any) -> bool:
    return isinstance(v, tuple) and len(v) == 2 and v[0] == 'string'


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_symbol(v: Any) -> bool:
    return isinstance(v, str)


def _make_builtin(name, fn):
    return ('builtin', name, fn)


def _to_list(v):
    """把内部表示的列表转成 Python list，要求是真列表。"""
    result = []
    while _is_pair(v):
        result.append(v[1])
        v = v[2]
    if not _is_nil(v):
        raise TypeError("不是真列表")
    return result


def _from_list(pylist):
    """把 Python list 转成内部表示的真列表。"""
    result = ('nil',)
    for item in reversed(pylist):
        result = ('pair', item, result)
    return result


def _arith(op, args, name):
    if not args:
        raise TypeError(f"{name} 至少需要 1 个参数")
    if not all(_is_number(a) for a in args):
        raise TypeError(f"{name} 的参数必须都是数字")
    return op(args)


def _add(args):
    return _arith(lambda a: sum(a), args, '+')


def _sub(args):
    if len(args) == 1:
        return -args[0]
    return _arith(lambda a: a[0] - sum(a[1:]), args, '-')


def _mul(args):
    return _arith(lambda a: __import__('math').prod(a), args, '*')


def _trunc_div(a: int, b: int) -> int:
    """整数除法，商向零截断（纯整数运算，不经过浮点）。"""
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def _div(args):
    if len(args) == 1:
        x = args[0]
        if not _is_number(x):
            raise TypeError("/ 的参数必须是数字")
        return 1 / x
    if not all(_is_number(a) for a in args):
        raise TypeError("/ 的参数必须都是数字")
    result = args[0]
    for x in args[1:]:
        if isinstance(result, int) and isinstance(x, int):
            # 整数相除得整数商，负数商向零截断
            result = _trunc_div(result, x)
        else:
            result = result / x
    return result


def _modulo(args):
    if len(args) != 2:
        raise TypeError("modulo 需要 2 个参数")
    a, b = args
    if not (_is_number(a) and _is_number(b)):
        raise TypeError("modulo 的参数必须都是数字")
    return a % b


def _quotient(args):
    if len(args) != 2:
        raise TypeError("quotient 需要 2 个参数")
    a, b = args
    if not (_is_number(a) and _is_number(b)):
        raise TypeError("quotient 的参数必须都是数字")
    return _trunc_div(a, b)


def _expt(args):
    if len(args) != 2:
        raise TypeError("expt 需要 2 个参数")
    base, exp = args
    if not (_is_number(base) and _is_number(exp)):
        raise TypeError("expt 的参数必须都是数字")
    return base ** exp


def _abs(args):
    if len(args) != 1:
        raise TypeError("abs 需要 1 个参数")
    if not _is_number(args[0]):
        raise TypeError("abs 的参数必须是数字")
    return abs(args[0])


def _compare(op, args, name):
    if len(args) < 2:
        raise TypeError(f"{name} 至少需要 2 个参数")
    # 支持数字与符号，但参数必须是同一类型
    all_num = all(_is_number(a) for a in args)
    all_sym = all(_is_symbol(a) for a in args)
    if not (all_num or all_sym):
        raise TypeError(f"{name} 的参数必须都是数字或都是符号")
    return all(op(args[i], args[i + 1]) for i in range(len(args) - 1))


def _not(args):
    if len(args) != 1:
        raise TypeError("not 需要 1 个参数")
    return args[0] is False


def _cons(args):
    if len(args) != 2:
        raise TypeError("cons 需要 2 个参数")
    return ('pair', args[0], args[1])


def _car(args):
    if len(args) != 1:
        raise TypeError("car 需要 1 个参数")
    if not _is_pair(args[0]):
        raise TypeError("car 的参数必须是点对")
    return args[0][1]


def _cdr(args):
    if len(args) != 1:
        raise TypeError("cdr 需要 1 个参数")
    if not _is_pair(args[0]):
        raise TypeError("cdr 的参数必须是点对")
    return args[0][2]


def _list(args):
    return _from_list(args)


def _length(args):
    if len(args) != 1:
        raise TypeError("length 需要 1 个参数")
    return len(_to_list(args[0]))


def _append(args):
    result = []
    for lst in args:
        result.extend(_to_list(lst))
    return _from_list(result)


def _null_p(args):
    if len(args) != 1:
        raise TypeError("null? 需要 1 个参数")
    return _is_nil(args[0])


def _pair_p(args):
    if len(args) != 1:
        raise TypeError("pair? 需要 1 个参数")
    return _is_pair(args[0])


def _list_p(args):
    if len(args) != 1:
        raise TypeError("list? 需要 1 个参数")
    v = args[0]
    while _is_pair(v):
        v = v[2]
    return _is_nil(v)


def _number_p(args):
    if len(args) != 1:
        raise TypeError("number? 需要 1 个参数")
    return _is_number(args[0])


def _boolean_p(args):
    if len(args) != 1:
        raise TypeError("boolean? 需要 1 个参数")
    return isinstance(args[0], bool)


def _symbol_p(args):
    if len(args) != 1:
        raise TypeError("symbol? 需要 1 个参数")
    return _is_symbol(args[0])


def _string_p(args):
    if len(args) != 1:
        raise TypeError("string? 需要 1 个参数")
    return _is_string(args[0])


def _procedure_p(args):
    if len(args) != 1:
        raise TypeError("procedure? 需要 1 个参数")
    v = args[0]
    return (isinstance(v, tuple) and len(v) == 3 and v[0] == 'builtin') or \
           (isinstance(v, tuple) and len(v) == 4 and v[0] == 'closure')


def _zero_p(args):
    if len(args) != 1:
        raise TypeError("zero? 需要 1 个参数")
    if not _is_number(args[0]):
        raise TypeError("zero? 的参数必须是数字")
    return args[0] == 0


def _even_p(args):
    if len(args) != 1:
        raise TypeError("even? 需要 1 个参数")
    if not _is_number(args[0]):
        raise TypeError("even? 的参数必须是数字")
    return args[0] % 2 == 0


def _odd_p(args):
    if len(args) != 1:
        raise TypeError("odd? 需要 1 个参数")
    if not _is_number(args[0]):
        raise TypeError("odd? 的参数必须是数字")
    return args[0] % 2 != 0


def _eq_p(args):
    if len(args) != 2:
        raise TypeError("eq? 需要 2 个参数")
    a, b = args
    # 符号、数字、布尔按值比较；复合数据按同一性
    if _is_number(a) and _is_number(b):
        return a == b
    if isinstance(a, bool) and isinstance(b, bool):
        return a is b
    if _is_symbol(a) and _is_symbol(b):
        return a == b
    # 其余情况（含字符串、点对、过程）按同一性
    return a is b


def _equal_p(args):
    if len(args) != 2:
        raise TypeError("equal? 需要 2 个参数")
    return _equal(args[0], args[1])


def _equal(a, b):
    """结构相等：逐层比较，先比较类型再比较值。"""
    # 布尔和数字要区分开（Python 里 True == 1）
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if _is_number(a) and _is_number(b):
        return a == b
    if _is_symbol(a) and _is_symbol(b):
        return a == b
    if _is_string(a) and _is_string(b):
        return a[1] == b[1]
    if _is_nil(a) and _is_nil(b):
        return True
    if _is_pair(a) and _is_pair(b):
        return _equal(a[1], b[1]) and _equal(a[2], b[2])
    # 类型不同
    if _is_number(a) != _is_number(b) or \
       _is_symbol(a) != _is_symbol(b) or \
       _is_string(a) != _is_string(b) or \
       _is_pair(a) != _is_pair(b) or \
       _is_nil(a) != _is_nil(b):
        return False
    return a == b


def _display(args):
    if len(args) != 1:
        raise TypeError("display 需要 1 个参数")
    print(display_to_string(args[0]), end='')
    return None


def _newline(args):
    if len(args) != 0:
        raise TypeError("newline 不需要参数")
    print()
    return None


def _make_env():
    """构造包含全部内置过程的初始环境字典。"""
    env = {}
    # 算术
    env['+'] = _make_builtin('+', _add)
    env['-'] = _make_builtin('-', _sub)
    env['*'] = _make_builtin('*', _mul)
    env['/'] = _make_builtin('/', _div)
    env['modulo'] = _make_builtin('modulo', _modulo)
    env['quotient'] = _make_builtin('quotient', _quotient)
    env['expt'] = _make_builtin('expt', _expt)
    env['abs'] = _make_builtin('abs', _abs)
    # 比较
    env['='] = _make_builtin('=', lambda a: _compare(lambda x, y: x == y, a, '='))
    env['<'] = _make_builtin('<', lambda a: _compare(lambda x, y: x < y, a, '<'))
    env['>'] = _make_builtin('>', lambda a: _compare(lambda x, y: x > y, a, '>'))
    env['<='] = _make_builtin('<=', lambda a: _compare(lambda x, y: x <= y, a, '<='))
    env['>='] = _make_builtin('>=', lambda a: _compare(lambda x, y: x >= y, a, '>='))
    # 布尔
    env['not'] = _make_builtin('not', _not)
    # 列表
    env['cons'] = _make_builtin('cons', _cons)
    env['car'] = _make_builtin('car', _car)
    env['cdr'] = _make_builtin('cdr', _cdr)
    env['list'] = _make_builtin('list', _list)
    env['length'] = _make_builtin('length', _length)
    env['append'] = _make_builtin('append', _append)
    env['null?'] = _make_builtin('null?', _null_p)
    env['pair?'] = _make_builtin('pair?', _pair_p)
    env['list?'] = _make_builtin('list?', _list_p)
    # 谓词
    env['number?'] = _make_builtin('number?', _number_p)
    env['boolean?'] = _make_builtin('boolean?', _boolean_p)
    env['symbol?'] = _make_builtin('symbol?', _symbol_p)
    env['string?'] = _make_builtin('string?', _string_p)
    env['procedure?'] = _make_builtin('procedure?', _procedure_p)
    env['zero?'] = _make_builtin('zero?', _zero_p)
    env['even?'] = _make_builtin('even?', _even_p)
    env['odd?'] = _make_builtin('odd?', _odd_p)
    env['eq?'] = _make_builtin('eq?', _eq_p)
    env['equal?'] = _make_builtin('equal?', _equal_p)
    # 输出
    env['display'] = _make_builtin('display', _display)
    env['newline'] = _make_builtin('newline', _newline)
    return env
