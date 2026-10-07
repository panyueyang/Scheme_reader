"""求值器：mini-Scheme 解释器的心脏。

核心是两个互相递归的函数：
    evaluate(expr, env)  —— 求值一个表达式
    apply(proc, args)    —— 调用一个过程

值的内部表示约定与 printer/builtins 一致：
    - 数字 / 布尔 → Python 原生值
    - 字符串 → ('string', "内容")
    - 符号 → Python str
    - 点对 → ('pair', car, cdr)
    - 空表 → ('nil',)
    - 内置过程 → ('builtin', name, fn)
    - 用户过程 → ('closure', params, body, env)
"""

from typing import Any, List
from environment import Environment


def evaluate(expr: Any, env: Environment) -> Any:
    """求值一个表达式。

    Args:
        expr: 表达式（解析器产生的嵌套结构）。
        env: 当前环境。

    Returns:
        求值结果。

    Raises:
        NameError: 变量未定义。
        TypeError: 类型错误（如把非过程当函数调用）。
    """
    # 自求值：数字、布尔、字符串、None
    if expr is None or isinstance(expr, (int, float, bool)):
        return expr
    if isinstance(expr, tuple) and len(expr) == 2 and expr[0] == 'string':
        return expr

    # 符号：去环境查值
    if isinstance(expr, str):
        return env.lookup(expr)

    # 列表：特殊形式或函数调用
    if isinstance(expr, list):
        if not expr:
            raise TypeError("空列表不能求值")
        op = expr[0]
        args = expr[1:]

        # 特殊形式
        if op == 'quote':
            return _eval_quote(args)
        if op == 'if':
            return _eval_if(args, env)
        if op == 'cond':
            return _eval_cond(args, env)
        if op == 'and':
            return _eval_and(args, env)
        if op == 'or':
            return _eval_or(args, env)
        if op == 'define':
            return _eval_define(args, env)
        if op == 'lambda':
            return _eval_lambda(args, env)
        if op == 'let':
            return _eval_let(args, env)
        if op == 'begin':
            return _eval_begin(args, env)

        # 函数调用：先求值操作符和全部实参
        proc = evaluate(op, env)
        values = [evaluate(a, env) for a in args]
        return apply(proc, values)

    raise TypeError(f"无法求值的表达式: {expr!r}")


def apply(proc: Any, args: List[Any]) -> Any:
    """调用一个过程。

    Args:
        proc: 过程值（内置过程或闭包）。
        args: 已求值的实参列表。

    Returns:
        调用结果。
    """
    # 内置过程
    if isinstance(proc, tuple) and len(proc) == 3 and proc[0] == 'builtin':
        return proc[2](args)

    # 用户过程（闭包）
    if isinstance(proc, tuple) and len(proc) == 4 and proc[0] == 'closure':
        params, body, def_env = proc[1], proc[2], proc[3]
        if len(params) != len(args):
            raise TypeError(
                f"参数个数不匹配: 需要 {len(params)} 个，给了 {len(args)} 个")
        new_env = def_env.extend(params, args)
        # 函数体按 begin 语义求值
        result = None
        for e in body:
            result = evaluate(e, new_env)
        return result

    raise TypeError(f"不是过程，无法调用: {proc!r}")


# ---------- 特殊形式求值 ----------

def _eval_quote(args):
    """quote：原样返回数据，不求值。"""
    if len(args) != 1:
        raise TypeError("quote 需要 1 个参数")
    return _quote_to_value(args[0])


def _quote_to_value(expr):
    """把 quote 里的数据转成内部值表示。

    列表要转成点对链，符号保持字符串，数字/布尔/字符串保持原样。
    """
    if expr is None or isinstance(expr, (int, float, bool)):
        return expr
    if isinstance(expr, tuple) and len(expr) == 2 and expr[0] == 'string':
        return expr
    if isinstance(expr, str):
        return expr
    if isinstance(expr, list):
        if not expr:
            return ('nil',)
        # 递归转换列表元素，再拼成点对链
        result = ('nil',)
        for item in reversed(expr):
            result = ('pair', _quote_to_value(item), result)
        return result
    raise TypeError(f"quote 不支持的数据: {expr!r}")


def _eval_if(args, env):
    """if：先求值测试，再只走一个分支。"""
    if len(args) < 2 or len(args) > 3:
        raise TypeError("if 需要 2 或 3 个参数")
    test = evaluate(args[0], env)
    if test is not False:
        return evaluate(args[1], env)
    if len(args) == 3:
        return evaluate(args[2], env)
    return None


def _eval_cond(args, env):
    """cond：从上到下依次测试，命中后按 begin 语义求值。"""
    for clause in args:
        if not isinstance(clause, list) or not clause:
            raise TypeError("cond 子句必须是非空列表")
        test_expr = clause[0]
        body = clause[1:]

        if test_expr == 'else':
            # else 子句直接执行
            result = None
            for e in body:
                result = evaluate(e, env)
            return result

        test = evaluate(test_expr, env)
        if test is not False:
            if not body:
                return test
            result = None
            for e in body:
                result = evaluate(e, env)
            return result
    return None


def _eval_and(args, env):
    """and：短路求值，遇到 #f 立刻返回 #f。"""
    if not args:
        return True
    result = True
    for e in args:
        result = evaluate(e, env)
        if result is False:
            return False
    return result


def _eval_or(args, env):
    """or：短路求值，遇到非 #f 立刻返回它。"""
    if not args:
        return False
    for e in args:
        result = evaluate(e, env)
        if result is not False:
            return result
    return False


def _eval_define(args, env):
    """define：先求值右侧表达式，再在当前环境绑定。"""
    if len(args) < 2:
        raise TypeError("define 至少需要 2 个参数")

    target = args[0]
    # 函数简写形式 (define (f x ...) body ...)
    if isinstance(target, list):
        if not target or not isinstance(target[0], str):
            raise TypeError("define 的函数名必须是符号")
        name = target[0]
        params = target[1:]
        body = args[1:]
        env.define(name, ('closure', params, body, env))
        return name

    # 普通形式 (define x expr)
    if not isinstance(target, str):
        raise TypeError("define 的名字必须是符号")
    value = evaluate(args[1], env)
    env.define(target, value)
    return target


def _eval_lambda(args, env):
    """lambda：制造闭包，记住定义时的环境。"""
    if len(args) < 2:
        raise TypeError("lambda 至少需要参数表和函数体")
    params = args[0]
    if not isinstance(params, list) or not all(isinstance(p, str) for p in params):
        raise TypeError("lambda 的参数表必须是符号列表")
    body = args[1:]
    return ('closure', params, body, env)


def _eval_let(args, env):
    """let：并行绑定，先在外层环境求值所有表达式。"""
    if len(args) < 2:
        raise TypeError("let 至少需要绑定表和函数体")
    bindings = args[0]
    if not isinstance(bindings, list):
        raise TypeError("let 的绑定表必须是列表")

    names = []
    values = []
    for b in bindings:
        if not isinstance(b, list) or len(b) != 2:
            raise TypeError("let 的每个绑定必须是 (名 值) 形式")
        name, expr = b[0], b[1]
        if not isinstance(name, str):
            raise TypeError("let 的绑定名必须是符号")
        names.append(name)
        values.append(evaluate(expr, env))  # 在外层环境求值

    new_env = env.extend(names, values)
    result = None
    for e in args[1:]:
        result = evaluate(e, new_env)
    return result


def _eval_begin(args, env):
    """begin：从左到右依次求值，返回最后一个。"""
    result = None
    for e in args:
        result = evaluate(e, env)
    return result
