"""
Common domain model utilities.
"""

from collections.abc import Iterator
from typing import Any

from pydantic_core import core_schema

from src.domain_models.lean_canvas import LeanCanvas


class LazyIdeaIterator(Iterator[LeanCanvas]):
    """
    Wrapper for Idea Iterator to enforce single-use consumption and safety.

    This class is not a Pydantic model but used as a field type.
    """

    def __init__(self, iterator: Iterator[LeanCanvas]) -> None:
        self._iterator = iterator
        self._consumed = False

    def __iter__(self) -> Iterator[LeanCanvas]:
        # Return self as the iterator
        return self

    def __next__(self) -> LeanCanvas:
        # Delegate to the wrapped iterator
        if self._consumed:
            # Already marked as started
            pass
        self._consumed = True
        return next(self._iterator)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """
        Define schema for Pydantic V2 to handle this custom type.
        This allows 'strict=True' (extra="forbid") without arbitrary_types_allowed=True.
        """
        return core_schema.is_instance_schema(cls)
