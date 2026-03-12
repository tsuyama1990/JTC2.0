import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int) -> list[str]:
    """Helper to chunk text into smaller parts."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def scan_directory_size(path: str, depth_limit: int = 10) -> int:
    """
    Calculate directory size iteratively with depth limit and strict file count.

    Args:
        path: Path to scan.
        depth_limit: Maximum recursion depth.

    Returns:
        Total size in bytes.
    """
    total = 0
    file_count = 0
    MAX_FILES = 10000

    # Queue for BFS traversal: (path, current_depth)
    queue = [(path, 0)]

    # Track visited inodes to prevent loops via hardlinks/symlinks if followed (though we disable symlinks)
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
                        if file_count > MAX_FILES:
                            logger.warning(
                                f"Scan file limit ({MAX_FILES}) reached at {current_path}. returning partial size."
                            )
                            return total

                    elif entry.is_dir(follow_symlinks=False):
                        queue.append((entry.path, depth + 1))
        except OSError as e:
            logger.warning(f"Error scanning index directory {current_path}: {e}")

    return total

@lru_cache(maxsize=1)
def scan_directory_size_cached(path: str, depth_limit: int = 10, ttl_hash: int = 0) -> int:
    """
    Cached version of scan_directory_size.
    ttl_hash is a trick to invalidate cache by passing a changing value (like time // 60).
    """
    return scan_directory_size(path, depth_limit)
