"""Unit tests for updater helpers.

Run with:
    python -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from updater import _parse_version, _ps_single_quote


class ParseVersionTests(unittest.TestCase):
    def test_with_v_prefix(self) -> None:
        self.assertEqual(_parse_version("v1.2.3"), (1, 2, 3))

    def test_uppercase_v_prefix(self) -> None:
        self.assertEqual(_parse_version("V1.2.3"), (1, 2, 3))

    def test_no_prefix(self) -> None:
        self.assertEqual(_parse_version("1.0.0"), (1, 0, 0))

    def test_strips_trailing_garbage(self) -> None:
        self.assertEqual(_parse_version("v1.2.3-beta"), (1, 2, 3))

    def test_garbage_input_compares_less_than_real_version(self) -> None:
        # Contract: an unparseable tag must not be treated as newer than a real one.
        self.assertLess(_parse_version("xyz"), _parse_version("v1.0.0"))

    def test_versions_compare_correctly(self) -> None:
        self.assertGreater(_parse_version("v1.2.10"), _parse_version("v1.2.9"))
        self.assertGreater(_parse_version("v1.10.0"), _parse_version("v1.9.99"))
        self.assertEqual(_parse_version("v1.0.0"), _parse_version("1.0.0"))


class PsSingleQuoteTests(unittest.TestCase):
    def test_passthrough_no_quotes(self) -> None:
        path = r"C:\Users\justing\AppData\Local\ATS Inc\PhoenixMasterTool"
        self.assertEqual(_ps_single_quote(path), path)

    def test_escapes_single_quote(self) -> None:
        self.assertEqual(
            _ps_single_quote(r"C:\Users\O'Brien\foo"),
            r"C:\Users\O''Brien\foo",
        )

    def test_escapes_multiple_quotes(self) -> None:
        self.assertEqual(_ps_single_quote("a'b'c"), "a''b''c")

    def test_empty(self) -> None:
        self.assertEqual(_ps_single_quote(""), "")


if __name__ == "__main__":
    unittest.main()
