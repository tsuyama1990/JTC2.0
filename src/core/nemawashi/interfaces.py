from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class InfluenceNetworkInterface(Protocol):
    stakeholders: list[Any]
    matrix: Any
    topic: str

    @property
    def is_dense(self) -> bool: ...
