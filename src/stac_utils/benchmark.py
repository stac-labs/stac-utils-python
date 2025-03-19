import timeit
from functools import wraps


class Benchmark(object):
    """
    Measures execution time
    """

    def __init__(self, msg: str):
        """
        Initializes with message string
        """
        self.msg = msg

    def __enter__(self):
        """
        Starts timer and prints
        """
        print(f"Starting {self.msg}")
        self.start = timeit.default_timer()
        return self

    def __exit__(self, *args):
        """
        Exits and prints execution time
        """
        t = timeit.default_timer() - self.start
        print(make_msg(self.msg, t))
        self.time = t

    def current(self) -> float:
        """
        Returns execution time
        """
        t = timeit.default_timer() - self.start
        print(make_msg(self.msg, t))
        return t


def make_msg(msg: str, t: float) -> str:
    """
    Returns message with time in plain English
    """
    m, s = divmod(t, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d:
        msg = f"{msg}: {d:.0f} days, {h:.0f} hours, {m:.0f} minutes, {s:.0f} seconds"
    elif h:
        msg = f"{msg}: {h:.0f} hours, {m:.0f} minutes, {s:.0f} seconds"
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
