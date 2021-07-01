import typing
from typing import Any, Dict, KeysView, List, Optional, Type, Union

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


def match_type(value: Any, type_: Any) -> Result:
    # TODO: match all values in a list instead of only the first one
    # Basic types
    errors: Optional[List[str]] = []
    if type_ in [int, float, str, bool]:
        if not isinstance(value, type_):
            errors = [f"{value}: expected type {type_} but got {type(value)}"]
        return Result("basic type", errors)

    # Dicts
    elif isinstance(value, dict) and isinstance(type_, dict):
        v_fields, t_fields = value.keys(), type_.keys()

        # Compare the fields
        if v_fields - t_fields:
            errors.append(f"Value has more fields than type: {v_fields - t_fields}")
        if t_fields - v_fields:
            errors.append(f"Type has more fields than value: {t_fields - v_fields}")
        if errors:
            errors.append(f"Common fields: {t_fields & v_fields}")

        # Match recursively
        children = {}
        for field in v_fields & t_fields:
            match = match_type(value[field], type_[field])
            if match.has_errors:
                children[field] = match

        return Result("dict", errors, children)

    # Lists
    elif typing_inspect.get_origin(type_) == list:
        child = None

        if not isinstance(value, list):
            errors.append("Expected list")
        elif len(value) > 0:
            # Typecheck the last value
            tp = typing_inspect.get_args(type_)[0]
            match = match_type(value[0], tp)
            child = match if match.has_errors else None

        return Result("list", errors, child)

    # Union
    elif typing_inspect.is_union_type(type_):
        children = {}

        for tp in typing_inspect.get_args(type_):
            match = match_type(value, tp)
            if not match.has_errors:
                return Result("union")
            children[str(tp)] = match

        errors = ["None of the union types matched"]

        return Result("union", errors, children)

    # Page or CursorPage
    elif typing_inspect.get_origin(type_) in (json_types.Page, json_types.CursorPage):
        if typing_inspect.get_origin(type_) == json_types.Page:
            label = "page"
            page_fields = {"href", "items", "limit", "next", "offset", "previous", "total"}
        else:
            label = "cursor_page"
            page_fields = {"cursors", "href", "items", "limit", "next", "total"}

        # Basic checks
        if not isinstance(value, dict):
            return Result(label, [f"Expected {label} but {value} is not a dict"])
        if not "items" in value:
            return Result(label, [f"Value has no \"items\" field"])

        # Compare the fields
        if value.keys() - page_fields:
            errors.append(f"Value has more fields than type: {value.keys() - page_fields}")
        if page_fields - value.keys():
            errors.append(f"Type has more fields than value: {page_fields - value.keys()}")
        if errors:
            errors.append(f"Common fields: {page_fields & value.keys()}")

        child = None
        if len(value["items"]) > 0:
            # Match the first item
            nested = typing_inspect.get_args(type_)
            match = match_type(value["items"][0], nested[0])
            if match.has_errors:
                child = match
        return Result(label, errors, child)

    # TypedDicts
    elif typing_inspect.typed_dict_keys(type_):
        keys = typing.get_type_hints(type_)
        return Result(type_.__name__, children=match_type(value, keys))

    else:
        raise ValueError()


def pprint_result(result: Result, tabs: int = 0):
    print("  " * tabs, f"[{result.label}]")
    for error in result.error_messages:
        print("  " * tabs, "-", error)
    if isinstance(result.children, dict):
        for field, sub_result in result.children.items():
            if sub_result.has_errors:
                print("  " * tabs, field)
                pprint_result(sub_result, tabs+1)
    elif result.children is not None:
        if result.children.has_errors:
            pprint_result(result.children, tabs+1)


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


def typecheck_response(response, method):
    return_type = typing.get_type_hints(method)["return"]
    match = match_type(response, return_type)
    if match.has_errors:
        print("Tried to match value to:", return_type)
        pprint_result(match)
        print("Value doesn't match the type!")
    else:
        print("The value matches the type")


if __name__ == "__main__":
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    tracks = sp.playlist_items('3cEYpjA9oz9GiPac4AsH4n', additional_types=['track'])
    typecheck_response(tracks, sp.playlist_items)

    album = sp.album("4aawyAB9vmqN3uQ7FjRGTy")
    typecheck_response(album, sp.album)
    pass
