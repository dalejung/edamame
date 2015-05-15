edamame
=======

EDA..[mame](http://japanese.stackexchange.com/questions/8139/what-is-the-meaning-and-etymology-of-the-slang-word-%E3%81%BE%E3%82%81)

# NaginPy

So as of right now, the DSL-ish parts of edamame are being created in [naginpy](https://github.com/dalejung/naginpy). I have too many projects but I like making up names.

# quantreactor

More names and projects. I'm going to need to map this out on corkboard and threads.

# Speed
=======

* All operations should go through a central hub. This allows us to keep track of history and intermediate dataframes. 
* This would allow us to generate a manifest for all frames. Essentially some source frame with a chain of operations. This would serve as metadata and a unique ID. 
* Source frames would require some sort of unique ID to support this chain.
* All operations should be deferred if possible. They should return un-evaluated expressions masquerading as real objects.
* IF an operation, or set of operations, takes enough time to generate, the hub would automatically write to disk. Technically speaking, all we would need to recreate environment would be the source data and the manifest of operations.
* A deferred operation set would allow us to optimize the evaluation. Something as simple as `df1 + df2 + df3 + df4` could be optimized by doing them all in one pass or even reordering based on C vs F memory layout.
* We would want a whole bunch of metadata for operations. Things like how much data the operation needs access to like window sizes. The goal is having enough info for optimizing a complicated expression. Also would allow us to expose the operation parameters for things like a gui interface.
* Something like a shift shouldn't require we copy the data. It should just point to the pre-shifted frame.
* A frame shouldn't need to be consolidated. i.e. merging two dataframes together shouldn't need a new frame and be properly handled by the evaluater.
* Possible to do execution in the background during idle cycles. Maybe pre-computing things or taking pre-emptively changing a fortran array to c order?
* With the manfiest, we can store data in memory so re-executing a script over and over would not cost us processing, kind of like how ipython cells can save you execution, except done automatically.

# Expression

So thinking about this some more. Even if we can't defer an operation, we should always assume we're building up a manifest and then executing that against a specific data set. So in a normal pandas workflow of:

```python
df = generate_data()
df2 = df + 1
df3 = df2 * 2
```

`df3` is really a manifest of `+2, *2` that is applied to `df`. What is important here is that if everything is immutable, then we know that `df2 * 2 == (df + 1) * 2` or more importantly that `df2 == df + 1` which comes into play when dealing with caching and tracking data as it flows through analytical operations.

# Frontend
==========

* The view should be as dumb as possible. Follow the same hub rule above so we can track all action made by the user. Biggest thing is to be able to replicate what actions one took. Even something as simple as brushing/zooming should be tracked and essentialy replayable. 
* Need a language to describe interactivity. 
* Use the manifest of the data to expose ability to change paramters like groupby periods.

# Language
==========

* By taking over the import machinery and hooking into ipython, we can essentially create our own dsl. It would require that everything be valid python, but that is fine. Import machinery has already been tested for `datamodule`, not sure about hooking into ipython executition, but that should be fine.
* Could possible do things like hack the globals to temporarlyy populate with helpful vars. 

```
  import pandas as pd
  df = pd.util.testing.makeDataFrame()
  C = 1
  with dplyr(df) as res:
      group_by(A, B)
      summarize(total=sum(C))
      arrange(desc(D))

  # outside of with context, restore previous state
  assert 'A' not in globals()
  assert 'B' not in globals()
  assert 'group_by' not in globals()
  assert C == 1
  # manager.operations => [group_by(A,B), summarize(total=sum(C)), arrange(desc(D))]
```

* Figure out better primitives for data operations. Doing a complicated func for groupby or apply that hides a lot of context kind of sucks.
* Conceptually, if a user func uses all `edamame` compatible operations, we should be able to compile it down. We could pass in a frame and analyize the deferred operations/expression to see if we can optimize.

Essentially we should know that:
```
def user_func(df):
  return df + 1
```
can be run as one pass for
```
df.groupby(df.index).agg(user_func)
```

# Resources 

Just saw this: 

https://www.youtube.com/watch?v=lTOP_shhVBQ
