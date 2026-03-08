"""
Common domain model utilities.
"""

from collections.abc import Iterator

from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas

# Simply wrapping an iterator does not strictly necessitate overriding
# pydantic core schema if handled via arbitrary types explicitly in settings
# or converted upon assignment. We simplify the implementation.


def create_lazy_iterator(iterator: Iterator[LeanCanvas]) -> Iterator[LeanCanvas]:
    """
    Generator that acts as a safe, size-limited iterator for LeanCanvas items.
    """
    max_items = get_settings().iterator_safety_limit
    for count, item in enumerate(iterator):
        if count >= max_items:
            break
        yield item
