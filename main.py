"""mini-Scheme 解释器入口。

用法：
    python3 src/main.py file1.scm [file2.scm ...]   # 依次求值文件
    python3 src/main.py                             # 从标准输入读取
"""

import sys
import os

# 让解释器既能以 `python -m src.main` 也能以 `python src/main.py` 运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import tokenize
from parser import parse
from evaluator import evaluate
from primitives import _make_env
from environment import Environment
from printer import to_string


def run_source(source: str, env: Environment) -> None:
    """求值一段源代码，把每个顶层表达式的结果打印出来。

    结果为 None（无值）时不打印。
    """
    tokens = tokenize(source)
    exprs = parse(tokens)
    for expr in exprs:
        result = evaluate(expr, env)
        if result is not None:
            print(to_string(result))


def main():
    # 创建全局环境并装入内置过程
    global_env = Environment(_make_env())

    if len(sys.argv) > 1:
        # 从文件读取，多个文件共享同一个全局环境
        for path in sys.argv[1:]:
            with open(path, 'r', encoding='utf-8') as f:
                run_source(f.read(), global_env)
    else:
        # 从标准输入读取
        run_source(sys.stdin.read(), global_env)


if __name__ == '__main__':
    # 提高递归上限并在独立线程中加大栈空间，保证深层递归可用
    sys.setrecursionlimit(100000)
    import threading
    threading.stack_size(64 * 1024 * 1024)
    t = threading.Thread(target=main)
    t.start()
    t.join()
