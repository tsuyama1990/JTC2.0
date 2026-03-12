import logging
from collections.abc import Callable, Iterator

from llama_index.core import Document

from src.core.constants import ERR_RAG_TEXT_TOO_LARGE
from src.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

def chunk_text_generator(
    text: str | Iterator[str],
    source: str,
    chunk_size: int,
    max_doc_len: int,
    size_tracker_callback: Callable[[int], None]
) -> Iterator[Document]:
    """
    Yield documents from request content one by one.
    Tracks size updates via callback.
    """
    current_chunk_idx = 0

    def content_generator() -> Iterator[str]:
        if isinstance(text, str):
            if len(text) > max_doc_len:
                raise ValidationError(ERR_RAG_TEXT_TOO_LARGE.format(size=len(text)))
            yield text
        else:
            yield from text

    for content_part in content_generator():
        if not isinstance(content_part, str):
            logger.warning(f"Skipping non-string content in iterator from {source}")
            continue

        if len(content_part) > chunk_size:
            chunks = [
                content_part[i : i + chunk_size]
                for i in range(0, len(content_part), chunk_size)
            ]
        else:
            chunks = [content_part]

        for chunk in chunks:
            size_bytes = len(chunk.encode("utf-8"))
            size_tracker_callback(size_bytes)

            yield Document(
                text=chunk,
                metadata={"source": source, "chunk_index": current_chunk_idx},
            )
            current_chunk_idx += 1
