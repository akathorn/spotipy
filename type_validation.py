import typing
from typing import Any, Callable, Dict, KeysView, List, Optional, Type, Union

import typing_inspect

import spotipy
from spotipy import json_types
from spotipy.oauth2 import SpotifyClientCredentials


class Result:
    def __init__(self, label: str, errors: Optional[List[str]] = None,
                 children: Optional[Union[Dict[str, "Result"], "Result"]] = None) -> None:
        self.label = label
        self.error_messages = errors or []
        self.children = children or None  # don't store an empty dict

        if self.error_messages:
            self.has_errors = True
        elif isinstance(self.children, Result):
            self.has_errors = self.children.has_errors
        elif isinstance(self.children, dict):
            self.has_errors = any(child.has_errors for child in self.children.values())
        else:
            self.has_errors = False

    def pprint(self, tabs: int = 0):
        print("  " * tabs, f"[{self.label}]")
        for error in self.error_messages:
            print("  " * tabs, "-", error)
        if isinstance(self.children, dict):
            for field, sub_result in self.children.items():
                if sub_result.has_errors:
                    print("  " * tabs, field)
                    sub_result.pprint(tabs+1)
        elif self.children is not None:
            if self.children.has_errors:
                self.children.pprint(tabs+1)


class TypeChecker:
    def __init__(self) -> None:
        pass

    def match(self, value: Any, type_: Any) -> Result:
        if type_ in [int, float, str, bool]:
            return self.match_primitive(value, type_)
        elif isinstance(value, dict) and isinstance(type_, dict):
            return self.match_dict(value, type_)
        elif typing_inspect.get_origin(type_) == list or typing_inspect.get_origin(type_) == List:
            return self.match_list(value, typing_inspect.get_args(type_)[0])
        elif typing_inspect.is_union_type(type_):
            return self.match_union(value, type_)
        elif typing_inspect.get_origin(type_) in (json_types.Page, json_types.CursorPage):
            return self.match_page(value, type_)
        elif typing_inspect.typed_dict_keys(type_):
            return self.match_typeddict(value, type_)
        else:
            raise ValueError()

    def match_primitive(self, value: Union[int, float, str, bool], type_: Any) -> Result:
        if not isinstance(value, type_):
            Result("primitive", [f"{value}: expected type {type_} but got {type(value)}"])
        return Result("primitive")

    def match_list(self, list_: List[Any], nested_type: Any) -> Result:
        matches = [self.match(element, nested_type) for element in list_]
        error_matches = [match for match in matches if match.has_errors]

        if error_matches:
            errors = [f"{len(error_matches)} out of {len(list_)} elements don't match the type."]
            children = {"first error": error_matches[0]}
            return Result("list", errors, children)
        else:
            return Result("list")

    def match_union(self, value: Any, type_: Any) -> Result:
        children: Dict[str, Any] = {}

        for tp in typing_inspect.get_args(type_):
            match = self.match(value, tp)
            if not match.has_errors:
                return Result("union")
            children[tp.__name__] = match

        return Result("union", errors=["None of the union types matched"], children=children)

    def match_page(self,
                   value: Any,
                   type_: Union[json_types.Page[Any], json_types.CursorPage[Any]]) -> Result:
        errors: List[str] = []

        if typing_inspect.get_origin(type_) == json_types.Page:
            label = "page"
            fields = {"href", "items", "limit", "next", "offset", "previous", "total"}
        else:
            label = "cursor_page"
            fields = {"cursors", "href", "items", "limit", "next", "total"}

        # Basic checks
        if not isinstance(value, dict):
            return Result(label, [f"Expected {label} but {value} is not a dict"])

        # Compare the fields
        if value.keys() - fields:
            errors.append(f"Unrecognized keys: {value.keys() - fields}")
        if fields - value.keys():
            errors.append(f"Missing required key: {fields - value.keys()}")

        if errors:
            return Result(label, errors)

        nested_type = typing_inspect.get_args(type_)[0]
        nested_match = self.match_list(value["items"], nested_type)

        return Result(label, errors, children=nested_match)

    def match_typeddict(self, value: Dict[str, Any], type_: Any) -> Result:
        children: Dict[str, "Result"] = {}
        errors: List[str] = []

        # Every TypedDict T has a parent _T that defines the required keys
        super_type = getattr(json_types, "_" + type_.__name__)

        everything = typing.get_type_hints(type_)
        required = typing.get_type_hints(super_type)
        optional = {key: everything[key] for key in everything.keys() - required.keys()}

        if value.keys() - everything.keys():
            errors.append(f"Unrecognized keys: {list(value.keys() - everything.keys())}")

        children["required"] = self.match_dict(value, required)
        if optional:
            children["optional"] = self.match_dict(value, optional, optional=True)

        return Result(type_.__name__, errors=errors, children=children)

    def match_dict(self,
                   value: Dict[str, Any],
                   type_: Dict[str, Any],
                   optional: bool = False) -> Result:
        errors: List[str] = []
        v_fields, t_fields = value.keys(), type_.keys()

        # Compare the fields
        if not optional and t_fields - v_fields:
            errors.append(f"Missing required keys: {t_fields - v_fields}")

        # Match recursively
        children: Dict[str, "Result"] = {}
        for field in v_fields & t_fields:
            match = self.match(value[field], type_[field])
            if match.has_errors:
                children[field] = match

        return Result("dict", errors, children)


def simplify(v):
    if isinstance(v, list):
        return [simplify(v[0])] if len(v) > 0 else []
    elif isinstance(v, str):
        return "str"
    elif isinstance(v, int):
        return "int"
    elif isinstance(v, float):
        return "float"
    elif isinstance(v, bool):
        return "bool"
    elif v is None:
        return "None"
    elif isinstance(v, dict):
        new = dict()
        for key, value in v.items():
            new[key] = simplify(value)
        return new


def typecheck_response(response: Any, method: Any):
    checker = TypeChecker()
    return_type = typing.get_type_hints(method)["return"]
    match = checker.match(response, return_type)
    if match.has_errors:
        print("Tried to match value to:", return_type)
        match.pprint()
        print("Value doesn't match the type!")
    else:
        print("The value matches the type")


if __name__ == "__main__":
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    tracks = sp.playlist_items('3cEYpjA9oz9GiPac4AsH4n', additional_types=['track'])
    typecheck_response(tracks, sp.playlist_items)

    album = sp.album("4aawyAB9vmqN3uQ7FjRGTy")
    typecheck_response(album, sp.album)

    albums = sp.artist_albums("2cbWJP4X5b9sKEDW80uc5r")
    typecheck_response(albums, sp.artist_albums)
