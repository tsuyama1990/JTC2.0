import logging
import os
import re
import urllib.parse
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
            except (ValueError, TypeError) as e:
                import sys

                print(f"WARNING: Log mask string formatting failed: {e}", file=sys.stderr)  # noqa: T201

        return True


def validate_safe_path(path_str: str, allowed_rel_paths: list[str]) -> str:
    """
    Ensure persist directory is safe and absolute.
    Uses strict allowlist and pathlib.resolve(strict=True) for security.
    """
    if not path_str or not isinstance(path_str, str):
        msg = "Path must be a non-empty string."
        raise ConfigurationError(msg)

    # Fully decode URL-encoded paths to prevent bypass like %2e%2e/
    decoded_path = urllib.parse.unquote(path_str)

    # Normalize mixed slashes
    normalized_path = decoded_path.replace("\\", "/")

    # Reject explicit relative path traversal characters completely before processing
    if ".." in normalized_path:
        raise ConfigurationError(ERR_PATH_TRAVERSAL)

    path_obj = Path(normalized_path)
    if path_obj.is_symlink():
        msg = "Symlinks not allowed in persist_dir."
        raise ConfigurationError(msg)

    try:
        # Resolve the parent directory strictly to ensure it exists and isn't a symlink traversal,
        # then append the leaf node. This allows creating new directories safely.
        parent_path = path_obj.parent.resolve(strict=True)
        path = parent_path / path_obj.name

        cwd = Path.cwd().resolve(strict=True)
        allowed_parents = [(cwd / p).resolve() for p in allowed_rel_paths]
    except Exception as e:
        msg = f"Invalid path format, non-existent parent, or symlink: {e}"
        raise ConfigurationError(msg) from e

    is_safe = False
    for parent in allowed_parents:
        # Use commonpath to strictly ensure the path is a true child, avoiding prefix matching vulnerabilities
        try:
            if os.path.commonpath([str(parent), str(path)]) == str(parent):
                is_safe = True
                break
        except ValueError:
            # commonpath raises ValueError if paths are on different drives (Windows)
            pass

    if not is_safe:
        logger.error(f"Path Traversal Attempt: {path} is not in allowed parents {allowed_parents}")
        raise ConfigurationError(ERR_PATH_TRAVERSAL)

    return str(path)


def sanitize_query(query: str) -> str:
    """
    Sanitize input query to prevent injection or processing issues.
    Strips out non-printable characters and structural shell/SQL meta-characters
    to prevent command or query injection.
    """
    # Remove non-printable characters first
    printable_only = re.sub(r"[^\x20-\x7E\t\r\n\u0100-\uffff]", "", query)

    # Strip dangerous characters often used for injection:
    # ; (command chain), | (pipe), < > (redirects), ` (command sub), & (background/AND)
    # The auditor also wants general injection protection, so we escape or remove
    # dangerous control operators context-agnostically.
    sanitized = re.sub(r"[;|<>`&]", "", printable_only)

    return sanitized.strip()
