import textwrap
import typing
from typing import Any, Dict, List, Optional, Union

try:
    import typing_inspect
except ImportError as err:
    err.msg = "Module 'typing_inspect' is required to use the type-checker"
    raise err

from spotipy import json_types


class _TypeCheckingResult:
    def __init__(self, label: str, errors: Optional[List[str]] = None,
                 children: Optional[Union[Dict[str, "_TypeCheckingResult"], "_TypeCheckingResult"]] = None) -> None:
        self.label = label
        self.error_messages = errors or []
        self.children = children or None  # don't store an empty dict

        if self.error_messages:
            self.has_errors = True
        elif isinstance(self.children, _TypeCheckingResult):
            self.has_errors = self.children.has_errors
        elif isinstance(self.children, dict):
            self.has_errors = any(child.has_errors for child in self.children.values())
        else:
            self.has_errors = False

    def pprint(self, spaces: int = 0) -> str:
        result = [f"[{self.label}]"]

        for error in self.error_messages:
            result.append(f"  * {error}")

        if isinstance(self.children, dict):
            error_children = [
                (field, subresult) for field, subresult in self.children.items()
                if subresult.has_errors
            ]
            if error_children:
                result.append("  {")
                for field, subresult in error_children:
                    result.append(f"    {field}:")
                    result.append(subresult.pprint(6))
                result.append("  }")
        elif self.children is not None:
            if self.children.has_errors:
                result.append(self.children.pprint(2))

        return textwrap.indent("\n".join(result), " " * spaces)


class TypeChecker:
    def typecheck(self, value: Any, type_: Any) -> _TypeCheckingResult:
        if type_ in [int, float, str, bool]:
            return self._match_primitive(value, type_)
        elif isinstance(value, dict) and isinstance(type_, dict):
            return self._match_dict(value, type_)
        elif typing_inspect.get_origin(type_) == list or typing_inspect.get_origin(type_) == List:
            return self._match_list(value, typing_inspect.get_args(type_)[0])
        elif typing_inspect.is_union_type(type_):
            return self._match_union(value, type_)
        elif typing_inspect.get_origin(type_) in (json_types.Page, json_types.CursorPage):
            return self._match_page(value, type_)
        elif typing_inspect.typed_dict_keys(type_):
            return self._match_typeddict(value, type_)
        else:
            raise ValueError()

    def compare_with_signature(self, value: Any, function: Any):
        return_type = typing.get_type_hints(function)["return"]
        return self.typecheck(value, return_type)

    def _match_primitive(self, value: Union[int, float, str, bool], type_: Any) -> _TypeCheckingResult:
        if not isinstance(value, type_):
            return _TypeCheckingResult(
                "primitive", [f"{value}: expected type {type_} but got {type(value)}"])
        return _TypeCheckingResult("primitive")

    def _match_list(self, list_: List[Any], nested_type: Any) -> _TypeCheckingResult:
        if not isinstance(list_, list):
            return _TypeCheckingResult("list", ["The value is not a list"])

        matches = [self.typecheck(element, nested_type) for element in list_]
        error_matches = [match for match in matches if match.has_errors]

        if error_matches:
            errors = [f"{len(error_matches)} out of {len(list_)} elements don't match the type."]
            children = {"first error": error_matches[0]}
            return _TypeCheckingResult("list", errors, children)
        else:
            return _TypeCheckingResult("list")

    def _match_union(self, value: Any, type_: Any) -> _TypeCheckingResult:
        children: Dict[str, Any] = {}

        for tp in typing_inspect.get_args(type_):
            match = self.typecheck(value, tp)
            if not match.has_errors:
                return _TypeCheckingResult("union")
            children[tp.__name__] = match

        return _TypeCheckingResult("union", errors=["None of the union types matched"], children=children)

    def _match_page(self,
                    value: Any,
                    type_: Union[json_types.Page[Any], json_types.CursorPage[Any]]) -> _TypeCheckingResult:
        errors: List[str] = []

        if typing_inspect.get_origin(type_) == json_types.Page:
            label = "page"
            fields = {"href", "items", "limit", "next", "offset", "previous", "total"}
        else:
            label = "cursor_page"
            fields = {"cursors", "href", "items", "limit", "next", "total"}

        # Basic checks
        if not isinstance(value, dict):
            return _TypeCheckingResult(label, [f"Expected {label} but {value} is not a dict"])

        # Compare the fields
        if value.keys() - fields:
            errors.append(f"Unrecognized keys: {value.keys() - fields}")
        if fields - value.keys():
            errors.append(f"Missing required key: {fields - value.keys()}")

        if errors:
            return _TypeCheckingResult(label, errors)

        nested_type = typing_inspect.get_args(type_)[0]
        nested_match = self._match_list(value["items"], nested_type)

        return _TypeCheckingResult(label, errors, children=nested_match)

    def _match_typeddict(self, value: Dict[str, Any], type_: Any) -> _TypeCheckingResult:
        children: Dict[str, "_TypeCheckingResult"] = {}
        errors: List[str] = []

        all_hints = typing.get_type_hints(type_)
        if value.keys() - all_hints.keys():
            errors.append(f"Unrecognized keys: {list(value.keys() - all_hints.keys())}")

        # Some TypeDicts T have a parent _T that defines the required keys
        super_name = "_" + type_.__name__
        if hasattr(json_types, super_name):
            super_type = getattr(json_types, super_name)
            required = typing.get_type_hints(super_type)
            optional = {key: all_hints[key] for key in all_hints.keys() - required.keys()}
        elif type_.__total__:
            required = all_hints
            optional = {}
        else:
            required = {}
            optional = all_hints

        children["required"] = self._match_dict(value, required)
        if optional:
            children["optional"] = self._match_dict(value, optional, optional=True)

        return _TypeCheckingResult(type_.__name__, errors=errors, children=children)

    def _match_dict(self,
                    value: Dict[str, Any],
                    type_: Dict[str, Any],
                    optional: bool = False) -> _TypeCheckingResult:
        errors: List[str] = []
        v_fields, t_fields = value.keys(), type_.keys()

        # Compare the fields
        if not optional and t_fields - v_fields:
            errors.append(f"Missing required keys: {t_fields - v_fields}")

        # Match recursively
        children: Dict[str, "_TypeCheckingResult"] = {}
        for field in v_fields & t_fields:
            match = self.typecheck(value[field], type_[field])
            if match.has_errors:
                children[field] = match

        return _TypeCheckingResult("dict", errors, children)


if __name__ == "__main__":
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    typechecker = TypeChecker()

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth())

    album = sp.album("6oZo4eplmeaHSyEWO1tESm")
    print(typechecker.compare_with_signature(album, sp.track).pprint())

    track = sp.track("5yYDd5nBjyrOkiaDcQ58uf")
    print(typechecker.compare_with_signature(track, sp.album).pprint())
