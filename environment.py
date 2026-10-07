"""环境（变量绑定表）模块。

环境是一个字典加上指向外层环境的指针，实现词法作用域。
查找变量时从当前环境逐层向外找，直到找到为止。
"""


class Environment:
    """mini-Scheme 的词法环境。"""

    def __init__(self, bindings=None, parent=None):
        """创建一层新环境。

        Args:
            bindings: 初始绑定的 dict，可选。
            parent: 外层环境，None 表示全局环境。
        """
        self._data = dict(bindings) if bindings else {}
        self.parent = parent

    def lookup(self, name):
        """查找变量，找不到时抛 NameError。"""
        env = self
        while env is not None:
            if name in env._data:
                return env._data[name]
            env = env.parent
        raise NameError(f"未定义的变量: {name}")

    def define(self, name, value):
        """在当前环境绑定变量。"""
        self._data[name] = value

    def extend(self, names, values):
        """创建一层子环境，把 names 依次绑到 values 上。"""
        if len(names) != len(values):
            raise ValueError(
                f"参数个数不匹配: 需要 {len(names)} 个，给了 {len(values)} 个")
        return Environment(dict(zip(names, values)), parent=self)
