"""Tests for settings parsing."""

import unittest

from settings import parse_port


class ParsePortTests(unittest.TestCase):
    """Cover established parse_port behavior."""

    def test_parses_port(self) -> None:
        self.assertEqual(parse_port("8080"), 8080)

    def test_rejects_malformed_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid port"):
            parse_port("http")


if __name__ == "__main__":
    unittest.main()
