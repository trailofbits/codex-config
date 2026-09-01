"""Supported Python runtime checks."""


def is_supported(version: tuple[int, int]) -> bool:
    """Return whether a Python major/minor version is supported."""
    return (3, 12) <= version <= (3, 12)
