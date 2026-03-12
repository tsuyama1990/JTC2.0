import logging
import os
from pathlib import Path

from src.core.constants import ERR_PATH_TRAVERSAL
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SecretMaskerFilter(logging.Filter):
    """
    Globally masks sensitive API keys in all log outputs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.secrets = []
        # Add common sensitive env vars to the mask list
        for key in ["OPENAI_API_KEY", "TAVILY_API_KEY", "V0_API_KEY"]:
            val = os.getenv(key)
            if val and len(val) > 4:
                self.secrets.append(val)

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.secrets or not isinstance(record.msg, str):
            return True

        for secret in self.secrets:
            if secret in record.msg:
                # Mask secret, keeping first 4 and last 4 characters visible if long enough
                masked = f"{secret[:4]}***{secret[-4:]}" if len(secret) > 10 else "***"
                record.msg = record.msg.replace(secret, masked)

        # Also check formatted string if args exist
        if hasattr(record, "args") and record.args:
            try:
                formatted_msg = record.getMessage()
                for secret in self.secrets:
                    if secret in formatted_msg:
                        masked = f"{secret[:4]}***{secret[-4:]}" if len(secret) > 10 else "***"
                        formatted_msg = formatted_msg.replace(secret, masked)
                record.msg = formatted_msg
                record.args = ()  # Clear args since msg is fully formatted
            except Exception: # noqa: S110
                # Silently fail string formatting fallback; do not log here to avoid recursive loop
                pass

        return True


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
