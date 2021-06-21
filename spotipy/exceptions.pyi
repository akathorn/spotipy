from typing import Any, Optional

class SpotifyException(Exception):
    http_status: Any = ...
    code: Any = ...
    msg: Any = ...
    reason: Any = ...
    headers: Any = ...
    def __init__(self, http_status: Any, code: Any, msg: Any, reason: Optional[Any] = ..., headers: Optional[Any] = ...) -> None: ...
