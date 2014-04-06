import inspect
import gc
import sys
import os.path
from collections import OrderedDict

import pandas as pd

def is_property(code):
    """
    Using some CPython gc magics, check if a code object is a property

    gc idea taken from trace.py from stdlib
    """
    ## use of gc.get_referrers() was suggested by Michael Hudson
    # all functions which refer to this code object
    funcs = [f for f in gc.get_referrers(code)
                    if inspect.isfunction(f)]
    if len(funcs) != 1:
        return False

    # property object will reference the original func
    props = [p for p in gc.get_referrers(funcs[0])
                    if isinstance(p, property)]
    return len(props) == 1


class Follow(object):
    """
    Follows execution path.

    Meant as a quick way to see what a function does.

    In [2]: with Follow() as f:
    ...:     df.sum()
    ...:

    In [3]: f.pprint(depth=2)
    stat_func generic.py:3542
        _reduce frame.py:3995
            _get_axis_number generic.py:285
            _get_agg_axis frame.py:4128
            as_matrix generic.py:1938
    """
    def __init__(self, *args):
        self.timings = []
        self.frame_cache = {}
        self._caller_cache = {}

    def trace_dispatch(self, frame, event, arg):
        if event not in ['call', 'c_call']:
            return

        # skip built in funcs
        if inspect.isbuiltin(arg):
            return

        # skip properties, we're only really interested in function calls
        # this will unfortunently skip any important logic that is wrapped
        # in property logic
        code = frame.f_code
        if is_property(code):
            return

        indent, first_parent = self.indent_level(frame)
        f = frame.f_back
        if event == "c_call":
            func_name = arg.__name__
            fn = (indent, "", 0, func_name, id(frame),id(first_parent))
        elif event == 'call':
            fcode = frame.f_code
            fn = (indent, fcode.co_filename, fcode.co_firstlineno, fcode.co_name, id(frame), id(first_parent))

        self.timings.append(fn)

    def indent_level(self, frame):
        i = 0
        f = frame.f_back
        first_parent = f
        while f:
            if id(f) in self.frame_cache:
                i += 1
            f = f.f_back
        if i == 0:
            # clear out the frame cache
            self.frame_cache = {id(frame): True}
        else:
            self.frame_cache[id(frame)] = True
        return i, first_parent

    def to_frame(self):
        data = self.timings
        cols = ['indent', 'filename', 'lineno', 'func_name', 'frame_id', 'parent_id']
        df = pd.DataFrame(data, columns=cols)
        df.loc[:, 'filename'] = df.filename.apply(lambda s: os.path.basename(s))
        return df

    def __enter__(self):
        sys.setprofile(self.trace_dispatch)
        return self

    def __exit__(self, type, value, traceback):
        sys.setprofile(None)

    def file_module_function_of(self, frame):
        code = frame.f_code
        filename = code.co_filename
        if filename:
            modulename = modname(filename)
        else:
            modulename = None

        funcname = code.co_name
        clsname = None
        if code in self._caller_cache:
            if self._caller_cache[code] is not None:
                clsname = self._caller_cache[code]
        else:
            self._caller_cache[code] = None
            ## use of gc.get_referrers() was suggested by Michael Hudson
            # all functions which refer to this code object
            funcs = [f for f in gc.get_referrers(code)
                         if inspect.isfunction(f)]
            # require len(func) == 1 to avoid ambiguity caused by calls to
            # new.function(): "In the face of ambiguity, refuse the
            # temptation to guess."
            if len(funcs) == 1:
                dicts = [d for d in gc.get_referrers(funcs[0])
                             if isinstance(d, dict)]
                if len(dicts) == 1:
                    classes = [c for c in gc.get_referrers(dicts[0])
                                   if hasattr(c, "__bases__")]
                    if len(classes) == 1:
                        # ditto for new.classobj()
                        clsname = classes[0].__name__
                        # cache the result - assumption is that new.* is
                        # not called later to disturb this relationship
                        # _caller_cache could be flushed if functions in
                        # the new module get called.
                        self._caller_cache[code] = clsname
        if clsname is not None:
            funcname = "%s.%s" % (clsname, funcname)

        return filename, modulename, funcname

    def pprint(self, depth=None):
        df = self.to_frame()
        mask = df.filename == ''
        mask = mask | df.func_name.isin(['<lambda>', '<genexpr>'])
        mask = mask | df.func_name.str.startswith('__')
        if depth:
            mask = mask | (df.indent > depth)

        MSG_FORMAT = "{indent}{func_name} {filename}:{lineno}"

        df = df.loc[~mask]
        def format(row):
            indent = row[0]
            filename = row[1]
            lineno = row[2]
            func_name = row[3]
            msg = MSG_FORMAT.format(indent=" "*indent*4, func_name=func_name,
                                    filename=filename, lineno=lineno)
            return msg

        df = df.reset_index(drop=True)

        output = df.apply(format, axis=1, raw=True)

        for s in output.values:
            print s
