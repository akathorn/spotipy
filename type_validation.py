import typing
from pprint import pprint
from typing import Dict, List

import typing_inspect

import spotipy
from spotipy import json_types
from spotipy.oauth2 import SpotifyClientCredentials

Result = typing.NamedTuple("Result", label=str, errors=List[str], fields=Dict[str, "Result"])


def matches_type(value, type_) -> Result:
    # Basic types
    if type_ in [int, float, str, bool]:
        if isinstance(value, type_):
            return Result("basic type", [], {})
        else:
            return Result("basic type", [f"{value}: {type(value)}!={type_}"], {})
    # Dicts
    elif isinstance(value, dict) and isinstance(type_, dict):
        errors = []
        v_fields, t_fields = value.keys(), type_.keys()
        # Compare the fields
        if v_fields - t_fields:
            errors.append(f"Value has more fields than type: {v_fields - t_fields}")
        if t_fields - v_fields:
            errors.append(f"Type has more fields than value: {t_fields - v_fields}")
        fields = {}
        for field in v_fields & t_fields:
            match = matches_type(value[field], type_[field])
            if match.errors:
                fields[field] = match
        return Result("dict", errors, fields)
    # Lists
    elif typing_inspect.get_origin(type_) == list:
        if not isinstance(value, list):
            return Result("list", [f"Expected list"], {})
        elif len(value) > 0:
            tp = typing_inspect.get_args(type_)[0]
            match = matches_type(value[0], tp)
            return Result("list", [], fields={"contents": match} if match.errors else {})
        else:
            return Result("list", [], {})
    # Union
    elif typing_inspect.is_union_type(type_):
        fields = {}
        for tp in typing_inspect.get_args(type_):
            fields[str(tp)] = matches_type(value, tp)
        return Result("union", [], fields)
    # Page
    elif typing_inspect.get_origin(type_) == json_types.Page:
        errors = []
        page_fields = {"href", "items", "limit", "next", "offset", "previous", "total"}
        if not isinstance(value, dict):
            return Result("page", [f"Expected Page but {value} is not a dict"], {})
        if not "items" in value:
            return Result("page", ["Value is not a page"], {})
        # Compare the fields
        if value.keys() - page_fields:
            errors.append(f"Value has more fields than type: {value.keys() - page_fields}")
        if page_fields - value.keys():
            errors.append(f"Type has more fields than value: {page_fields - value.keys()}")
        fields = {}
        if len(value["items"]) > 0:
            nested = typing_inspect.get_args(type_)
            match = matches_type(value["items"][0], nested[0])
            if match.errors:
                fields["nested"] = match
        return Result("page", errors, fields=fields)
    elif typing_inspect.get_origin(type_) == json_types.CursorPage:
        errors = []
        cursor_fields = {"cursors", "href", "items", "limit", "next", "total"}
        if not isinstance(value, dict):
            return Result("cursor", [f"Expected Page but {value} is not a dict"], {})
        # Compare the fields
        if value.keys() - cursor_fields:
            errors.append(f"Value has more fields than type: {value.keys() - cursor_fields}")
        if cursor_fields - value.keys():
            errors.append(f"Type has more fields than value: {cursor_fields - value.keys()}")
        fields = {}
        if len(value["items"]) > 0:
            nested = typing_inspect.get_args(type_)
            match = matches_type(value["items"][0], nested[0])
            if match.errors:
                fields["nested"] = match
        return Result("cursor", errors, fields=fields)
    elif typing_inspect.typed_dict_keys(type_):
        keys = typing.get_type_hints(type_)
        match = matches_type(value, keys)
        return Result(str(type_), [], fields={"contents": match} if match.errors else {})
    else:
        raise Exception()


def pprint_result(result: Result, tabs=0):
    print("  " * tabs, f"[{result.label}]")
    for error in result.errors:
        print("  " * tabs, "-", error)
    for field, result in result.fields.items():
        print("  " * tabs, field)
        pprint_result(result, tabs+1)


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


if __name__ == "__main__":
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    pl_id = ' spotify:playlist:3cEYpjA9oz9GiPac4AsH4n'
    tracks = sp.playlist_items(pl_id, additional_types=['track'])
    album = sp.album("4aawyAB9vmqN3uQ7FjRGTy")
    # pprint(simplify(tracks))
    return_type = typing.get_type_hints(sp.playlist_items)["return"]
    matches_type(tracks, return_type)
    pass
