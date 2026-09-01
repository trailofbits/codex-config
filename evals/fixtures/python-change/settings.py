"""Settings parsing helpers."""


def parse_port(value: str) -> int:
    """Parse a TCP port from a decimal string."""
    try:
        port = int(value)
    except ValueError as error:
        raise ValueError(f"invalid port: {value!r}") from error

    if port < 0 or port > 65_535:
        raise ValueError(f"port out of range: {value!r}")
    return port
