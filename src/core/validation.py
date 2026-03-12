import logging

from src.core.constants import ERR_RAG_INDEX_SIZE

logger = logging.getLogger(__name__)


def validate_index_size(current_size_bytes: int, limit_mb: int) -> None:
    """Check if the tracked index size is too large."""
    limit_bytes = limit_mb * 1024 * 1024

    if current_size_bytes > limit_bytes:
        msg = ERR_RAG_INDEX_SIZE.format(limit=limit_mb)
        logger.error(msg)
        raise MemoryError(msg)
