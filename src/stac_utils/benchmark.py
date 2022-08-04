import timeit
from functools import wraps


class Benchmark(object):
    def __init__(self, msg: str):
        self.msg = msg

    def __enter__(self):
        print(f"Starting {self.msg}")
        self.start = timeit.default_timer()
        return self

    def __exit__(self, *args):
        t = timeit.default_timer() - self.start
        print(make_msg(self.msg, t))
        self.time = t

    def current(self):
        t = timeit.default_timer() - self.start
        print(make_msg(self.msg, t))
        return t


def make_msg(msg, t):
    m, s = divmod(t, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d:
        msg = (
            f"{msg}: {d:.0f} days, " f"{h:.0f} hours, {m:.0f} minutes, {s:.0f} seconds"
        )
    elif h:
        msg = f"{msg}: " f"{h:.0f} hours, {m:.0f} minutes, {s:.0f} seconds"
    elif m:
        msg = f"{msg}: {m:.0f} minutes, {s:.0f} seconds"
    else:
        msg = f"{msg}: {s:.3f} seconds"

    return msg


def benchmark(method):
    @wraps(method)
    def f(*args, **kwargs):
        start = timeit.default_timer()
        print(f"Starting {method.__name__}")
        result = method(*args, **kwargs)
        t = timeit.default_timer() - start
        print(make_msg(method.__name__, t))
        return result

    return f
