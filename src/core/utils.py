from collections.abc import Iterator


def chunk_text(text: str, chunk_size: int) -> Iterator[str]:
    """
    Split text into chunks of specified size efficiently.
    Uses generator to avoid loading list of chunks into memory.
    """
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
