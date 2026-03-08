import logging
import os
import time
from collections.abc import Iterator
from functools import lru_cache

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int) -> Iterator[str]:
    """
    Split text into chunks of specified size efficiently.
    Uses generator to avoid loading list of chunks into memory.
    """
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def sanitize_query(query: str) -> str:
    """
    Sanitize input query to prevent injection or processing issues.
    Efficient implementation using list comprehension.
    """
    chars = [ch for ch in query if (32 <= ord(ch) < 127) or ch in "\t\r\n" or ord(ch) > 127]
    return "".join(chars).strip()


def rate_limit(last_call_time: float, min_interval: float) -> float:
    """Simple blocking rate limiter. Returns the new last_call_time."""
    current = time.time()
    elapsed = current - last_call_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    return time.time()


def calculate_bytes_from_mb(mb: int) -> int:
    """Calculate byte size from MB."""
    return mb * 1024 * 1024


def _scan_dir_size(path: str, depth_limit: int = 10, max_files: int = 10000) -> int:
    """
    Calculate directory size iteratively with depth limit and strict file count.
    """
    total = 0
    file_count = 0

    # Queue for BFS traversal: (path, current_depth)
    queue = [(path, 0)]

    # Track visited inodes to prevent loops via hardlinks/symlinks
    visited_inodes = set()

    while queue:
        current_path, depth = queue.pop(0)

        if depth > depth_limit:
            continue

        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        stat = entry.stat()
                        if stat.st_ino in visited_inodes:
                            continue
                        visited_inodes.add(stat.st_ino)

                        total += stat.st_size
                        file_count += 1
                        if file_count > max_files:
                            logger.warning(
                                f"Scan file limit ({max_files}) reached at {current_path}. returning partial size."
                            )
                            return total

                    elif entry.is_dir(follow_symlinks=False):
                        queue.append((entry.path, depth + 1))
        except OSError as e:
            logger.warning(f"Error scanning index directory {current_path}: {e}")

    return total


@lru_cache(maxsize=1)
def get_rag_dir_size(
    path: str, depth_limit: int = 10, max_files: int = 10000, ttl_hash: int = 0
) -> int:
    """
    Cached version of directory size calculation.
    ttl_hash is a trick to invalidate cache by passing a changing value (like time // 60).
    """
    return _scan_dir_size(path, depth_limit, max_files)


def clear_rag_cache() -> None:
    """Clear the directory size cache."""
    get_rag_dir_size.cache_clear()


def validate_rag_query(question: str, max_len: int, err_msg_template: str) -> str:
    """Validate and sanitize RAG query."""
    if not isinstance(question, str):
        msg = "Query must be a string."
        raise TypeError(msg)

    if not question.strip():
        msg = "Query cannot be empty."
        raise ValueError(msg)

    question = sanitize_query(question)

    if len(question) > max_len:
        msg = err_msg_template.format(size=len(question))
        from src.core.exceptions import ValidationError

        raise ValidationError(msg)

    return question
