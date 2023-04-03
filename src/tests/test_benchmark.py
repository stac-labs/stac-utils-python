import contextlib
import io
import time
import unittest

from src.stac_utils.benchmark import make_msg, benchmark, Benchmark


class TestBenchmark(unittest.TestCase):
    def setUp(self) -> None:
        self.test_msg = "Foo"

    def test_make_msg(self):
        """Test make message"""

        cases = [
            # test value, expected response
            (42.111, f"{self.test_msg}: 42.111 seconds"),
            (42, f"{self.test_msg}: 42.000 seconds"),
            (42 + (2 * 60), f"{self.test_msg}: 2 minutes, 42 seconds"),
            (42.111 + (2 * 60), f"{self.test_msg}: 2 minutes, 42 seconds"),
            (
                42 + (2 * 60) + (3 * 60 * 60),
                f"{self.test_msg}: 3 hours, 2 minutes, 42 seconds",
            ),
            (
                42.111 + (2 * 60) + (3 * 60 * 60),
                f"{self.test_msg}: 3 hours, 2 minutes, 42 seconds",
            ),
            (
                42 + (2 * 60) + (3 * 60 * 60) + (4 * 60 * 60 * 24),
                f"{self.test_msg}: 4 days, 3 hours, 2 minutes, 42 seconds",
            ),
            (
                42.111 + (2 * 60) + (3 * 60 * 60) + (4 * 60 * 60 * 24),
                f"{self.test_msg}: 4 days, 3 hours, 2 minutes, 42 seconds",
            ),
        ]

        for test_value, expected_response in cases:
            self.assertEqual(expected_response, make_msg(self.test_msg, test_value))

    def test_benchmark_decorator(self):
        """Test benchmark decorator"""

        @benchmark
        def mock_func():
            time.sleep(0.1)

        test_print = io.StringIO()
        with contextlib.redirect_stdout(test_print):
            mock_func()

        # have to be a little inexact
        printed_string = test_print.getvalue().splitlines()
        self.assertIn("Starting mock_func", printed_string[0])
        self.assertIn("mock_func: 0.1", printed_string[1])

    def test_benchmark_class_init(self):
        """Test Benchmark class init"""

        test_print = io.StringIO()
        with contextlib.redirect_stdout(test_print):
            with Benchmark(self.test_msg):
                time.sleep(0.1)

        # have to be a little inexact
        self.assertIn(f"{self.test_msg}: 0.1", test_print.getvalue())

    def test_benchmark_class_context(self):
        """Test Benchmark class"""

        test_print = io.StringIO()
        with contextlib.redirect_stdout(test_print):
            with Benchmark(self.test_msg) as test_benchmark:
                time.sleep(0.1)
                self.assertGreaterEqual(test_benchmark.current(), 0.1)

        # have to be a little inexact
        self.assertIn(f"{self.test_msg}: 0.1", test_print.getvalue())


if __name__ == "__main__":
    unittest.main()
