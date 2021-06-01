import sys
from pathlib import Path

from line_profiler import LineProfiler as _LineProfiler
from line_profiler import show_func

class Profiler(object):
    """
    Attaches a LineProfiler to the passed in functions.

    In [113]: with Profiler(df.sum):
    .....:     df.sum()
    .....:
    Timer unit: 1e-06 s

    File: /Users/datacaliber/.virtualenvs/tepython/lib/python2.7/site-packages/pandas/core/generic.py
    Function: stat_func at line 3540
    Total time: 0.001618 s

    Line #      Hits         Time  Per Hit   % Time  Line Contents
    ==============================================================
    3540                                                       @Substitution(outname=name, desc=desc)
    3541                                                       @Appender(_num_doc)
    3542                                                       def stat_func(self, axis=None, skipna=None, level=None,
    3543                                                                     numeric_only=None, **kwargs):
    3544         1            7      7.0      0.4                  if skipna is None:
    3545         1            1      1.0      0.1                      skipna = True
    3546         1            1      1.0      0.1                  if axis is None:
    3547         1            3      3.0      0.2                      axis = self._stat_axis_number
    3548         1            1      1.0      0.1                  if level is not None:
    3549                                                               return self._agg_by_level(name, axis=axis, level=level,
    3550                                                                                         skipna=skipna)
    3551         1            2      2.0      0.1                  return self._reduce(f, axis=axis,
    3552         1         1603   1603.0     99.1                                      skipna=skipna, numeric_only=numeric_only)

    """
    def __init__(self, *args):
        self.profile = _LineProfiler()
        self.func_paths = {}

        if len(args) > 0:
            for func in args:
                if callable(func):
                    self.add_function(func)

    def add_function(self, func):
        if not hasattr(func, '__code__'):
            return
        module = func.__module__
        code = func.__code__
        filename = code.co_filename
        path = Path(filename)

        if not path.is_absolute():
            root_package = module.split('.')[0]
            root_module = sys.modules.get(root_package, None)
            root_path_init = Path(root_module.__file__)
            root_path = root_path_init.parent.parent
            abs_filename = root_path.joinpath(filename)
            self.func_paths[code.co_filename] = str(abs_filename)

        self.profile.add_function(func)

    def show_text(self, stats, unit, output_unit=None, stream=None, stripzeros=False):
        """
        Show text for the given timings.

        Largely a copy of line_profiler.show_text
        """
        if stream is None:
            stream = sys.stdout

        if output_unit is not None:
            stream.write('Timer unit: %g s\n\n' % output_unit)
        else:
            stream.write('Timer unit: %g s\n\n' % unit)

        for (fn, lineno, name), timings in sorted(stats.items()):
            # replace with absolute path for cython.
            abs_path = self.func_paths.get(fn, fn)
            show_func(abs_path, lineno, name, stats[fn, lineno, name], unit,
                output_unit=output_unit, stream=stream, stripzeros=stripzeros)


    def __enter__(self):
        self.profile.enable_by_count()

    def __exit__(self, type, value, traceback):
        self.profile.disable_by_count()

        lstats = self.profile.get_stats()
        self.show_text(lstats.timings, lstats.unit, output_unit=None, stream=None, stripzeros=False)
