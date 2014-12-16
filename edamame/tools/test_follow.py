import gc
import inspect
import edamame.tools.follow as follow
reload(follow)
get_parent = follow.get_parent

class Parent(object):
    def bob(self):
        pass

class TestClass(Parent):
    hi = '123'
    def __init__(self):
        pass

    def test_method(self, bob=123):
        pass

tc = TestClass()

import pandas as pd

df = pd.util.testing.makeDataFrame()

code = df._get_axis.im_func.func_code
code = tc.bob.im_func.func_code

parents = get_parent(code)
funcs = [f for f in gc.get_referrers(code)
                if inspect.isfunction(f)]

refs = [f for f in gc.get_referrers(funcs[0])]
for ref in refs:
    if isinstance(ref, dict):
        parents = [p for p in gc.get_referrers(ref) if isinstance(p, type)]
        if len(parents) == 1:
            p = parents[0]


with follow.Follow(3):
    tc.bob()
