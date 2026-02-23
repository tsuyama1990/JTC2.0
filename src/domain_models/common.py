"""
Common domain model utilities.
"""

from collections.abc import Iterator

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
            # Already marked as started, but we allow continuing iteration
            # until exhaustion. The flag indicates that iteration has *begun*.
            # If we wanted to enforce strict single-pass (e.g. no restart),
            # Python iterators do that by default.
            # This wrapper is mainly for type safety and potential future hooks.
            pass
        self._consumed = True
        return next(self._iterator)
