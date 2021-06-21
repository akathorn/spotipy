import sys
from typing import Any, Generic, List, Mapping, TypeVar, overload

if sys.version_info >= (3, 8):
    from typing import Literal, TypedDict
else:
    from typing_extensions import Literal, TypedDict

_T = TypeVar("_T", covariant=True)


class Page(Generic[_T], Mapping[str, Any]):
    # autopep8: off
    @overload
    def __getitem__(self, k: Literal["href"]) -> str: ...
    @overload
    def __getitem__(self, k: Literal["items"]) -> List[_T]: ...
    @overload
    def __getitem__(self, k: Literal["limit"]) -> int: ...
    @overload
    def __getitem__(self, k: Literal["next"]) -> str: ...
    @overload
    def __getitem__(self, k: Literal["offset"]) -> int: ...
    @overload
    def __getitem__(self, k: Literal["previous"]) -> str: ...
    @overload
    def __getitem__(self, k: Literal["total"]) -> int: ...

    def __getitem__(self, k: str) -> Any: ...
    # autopep8: on


class CursorPage(Generic[_T], Mapping[str, Any]):
    # autopep8: off
    @overload
    def __getitem__(self, k: Literal["cursors"]) -> "Cursor": ...
    @overload
    def __getitem__(self, k: Literal["href"]) -> str: ...
    @overload
    def __getitem__(self, k: Literal["items"]) -> List[_T]: ...
    @overload
    def __getitem__(self, k: Literal["limit"]) -> int: ...
    @overload
    def __getitem__(self, k: Literal["next"]) -> str: ...
    @overload
    def __getitem__(self, k: Literal["total"]) -> int: ...

    def __getitem__(self, k: str) -> Any: ...
    # autopep8: on