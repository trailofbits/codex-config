"""Tests for Python runtime support."""

import unittest

from runtime_support import is_supported


class RuntimeSupportTests(unittest.TestCase):
    """Cover the published runtime range."""

    def test_python_312_is_supported(self) -> None:
        self.assertTrue(is_supported((3, 12)))

    def test_python_311_is_not_supported(self) -> None:
        self.assertFalse(is_supported((3, 11)))


if __name__ == "__main__":
    unittest.main()
