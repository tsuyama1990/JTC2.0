"""
Common domain model utilities.
"""

from collections.abc import Iterator
from typing import Any

from pydantic_core import core_schema

from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas


class LazyIdeaIterator(Iterator[LeanCanvas]):
    """
    Wrapper for Idea Iterator to enforce single-use consumption and safety limits.

    This iterator ensures that we don't load infinite items or consume too much memory.
    It expects a generator or iterator as input.
    """

    def __init__(self, iterator: Iterator[LeanCanvas]) -> None:
        """
        Initialize the lazy iterator.

        Args:
            iterator: An iterator (preferably a generator) yielding LeanCanvas objects.
                      The iterator should NOT be pre-materialized list if possible.
        """
        self._iterator = iter(iterator)
        self._consumed = False
        self._count = 0
        self._max_items = get_settings().iterator_safety_limit

    def __iter__(self) -> Iterator[LeanCanvas]:
        return self

    def __next__(self) -> LeanCanvas:
        # Configurable hard limit if safety setting is not enough to stop unbounded exhaustion
        if self._count >= self._max_items:
            self._consumed = True
            msg = "LazyIdeaIterator reached configurable maximum items."
            raise StopIteration(msg)

        try:
            item = next(self._iterator)
        except StopIteration:
            self._consumed = True
            raise StopIteration from None

        self._count += 1
        return item

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        """
        Define schema for Pydantic V2 to handle this custom type.
        This allows 'strict=True' (extra="forbid") without arbitrary_types_allowed=True.
        """
        if source_type is not cls:
            msg = "Source type must be LazyIdeaIterator"
            raise TypeError(msg)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.list_schema(core_schema.any_schema()),
            python_schema=core_schema.is_instance_schema(cls),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: (
                    "LazyIdeaIterator(unconsumed)"
                    if not instance._consumed
                    else "LazyIdeaIterator(consumed)"
                )
            ),
        )
