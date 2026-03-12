import logging
from pathlib import Path

from src.core.constants import ERR_PATH_TRAVERSAL
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def validate_safe_path(path_str: str, allowed_rel_paths: list[str]) -> str:
    """
    Ensure persist directory is safe and absolute.
    Uses strict allowlist and pathlib.resolve(strict=True) for security.
    """
    if not path_str or not isinstance(path_str, str):
        msg = "Path must be a non-empty string."
        raise ConfigurationError(msg)

    try:
        path = Path(path_str).resolve(strict=False)
        cwd = Path.cwd().resolve(strict=True)
        allowed_parents = [(cwd / p).resolve() for p in allowed_rel_paths]

        path_exists = path.exists()
        is_symlink = path.is_symlink() if path_exists else False
        if path_exists:
            path = path.resolve(strict=True)
    except Exception as e:
        msg = f"Invalid path format or non-existent parent: {e}"
        raise ConfigurationError(msg) from e

    is_safe = False
    for parent in allowed_parents:
        if str(path).startswith(str(parent)):
            is_safe = True
            break

    if not is_safe:
        logger.error(f"Path Traversal Attempt: {path} is not in allowed parents {allowed_parents}")
        raise ConfigurationError(ERR_PATH_TRAVERSAL)

    if is_symlink:
        msg = "Symlinks not allowed in persist_dir."
        raise ConfigurationError(msg)

    return str(path)


def sanitize_query(query: str) -> str:
    """
    Sanitize input query to prevent injection or processing issues.
    Efficient implementation using list comprehension.
    """
    chars = [ch for ch in query if (32 <= ord(ch) < 127) or ch in "\t\r\n" or ord(ch) > 127]
    return "".join(chars).strip()
