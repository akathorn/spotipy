# -*- coding: utf-8 -*-

import typing
import unittest
from typing import Any, Dict, List, Optional, Union

import requests
import spotipy
import typing_inspect
from spotipy import (Spotify, SpotifyClientCredentials, SpotifyException,
                     json_types)


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


class _TypeChecker:
    def __init__(self) -> None:
        pass

    def match(self, value: Any, type_: Any) -> _TypeCheckingResult:
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

    def match_primitive(self, value: Union[int, float, str, bool], type_: Any) -> _TypeCheckingResult:
        if not isinstance(value, type_):
            _TypeCheckingResult(
                "primitive", [f"{value}: expected type {type_} but got {type(value)}"])
        return _TypeCheckingResult("primitive")

    def match_list(self, list_: List[Any], nested_type: Any) -> _TypeCheckingResult:
        matches = [self.match(element, nested_type) for element in list_]
        error_matches = [match for match in matches if match.has_errors]

        if error_matches:
            errors = [f"{len(error_matches)} out of {len(list_)} elements don't match the type."]
            children = {"first error": error_matches[0]}
            return _TypeCheckingResult("list", errors, children)
        else:
            return _TypeCheckingResult("list")

    def match_union(self, value: Any, type_: Any) -> _TypeCheckingResult:
        children: Dict[str, Any] = {}

        for tp in typing_inspect.get_args(type_):
            match = self.match(value, tp)
            if not match.has_errors:
                return _TypeCheckingResult("union")
            children[tp.__name__] = match

        return _TypeCheckingResult("union", errors=["None of the union types matched"], children=children)

    def match_page(self,
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
        nested_match = self.match_list(value["items"], nested_type)

        return _TypeCheckingResult(label, errors, children=nested_match)

    def match_typeddict(self, value: Dict[str, Any], type_: Any) -> _TypeCheckingResult:
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
        else:
            required = all_hints
            optional = {}

        children["required"] = self.match_dict(value, required)
        if optional:
            children["optional"] = self.match_dict(value, optional, optional=True)

        return _TypeCheckingResult(type_.__name__, errors=errors, children=children)

    def match_dict(self,
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
            match = self.match(value[field], type_[field])
            if match.has_errors:
                children[field] = match

        return _TypeCheckingResult("dict", errors, children)


def typecheck_response(response: Any, method: Any):
    checker = _TypeChecker()
    return_type = typing.get_type_hints(method)["return"]
    match = checker.match(response, return_type)
    if match.has_errors:
        print("Tried to match value to:", return_type.__class__)
        match.pprint()
        assert False, "Value doesn't match the type!"


class JSONTypeTest(unittest.TestCase):
    """
    These tests require client authentication - provide client credentials
    using the following environment variables

    ::

        'SPOTIPY_CLIENT_ID'
        'SPOTIPY_CLIENT_SECRET'
    """

    playlist = "spotify:user:plamere:playlist:2oCEWyyAPbZp9xhVSxZavx"
    four_tracks = ["spotify:track:6RtPijgfPKROxEzTHNRiDp",
                   "spotify:track:7IHOIqZUUInxjVkko181PB",
                   "4VrWlk8IQxevMvERoX08iC",
                   "http://open.spotify.com/track/3cySlItpiPiIAzU3NyHCJf"]

    two_tracks = ["spotify:track:6RtPijgfPKROxEzTHNRiDp",
                  "spotify:track:7IHOIqZUUInxjVkko181PB"]

    other_tracks = ["spotify:track:2wySlB6vMzCbQrRnNGOYKa",
                    "spotify:track:29xKs5BAHlmlX1u4gzQAbJ",
                    "spotify:track:1PB7gRWcvefzu7t3LJLUlf"]

    bad_id = 'BAD_ID'

    creep_urn = 'spotify:track:6b2oQwSGFkzsMtQruIWm2p'
    creep_id = '6b2oQwSGFkzsMtQruIWm2p'
    creep_url = 'http://open.spotify.com/track/6b2oQwSGFkzsMtQruIWm2p'
    el_scorcho_urn = 'spotify:track:0Svkvt5I79wficMFgaqEQJ'
    el_scorcho_bad_urn = 'spotify:track:0Svkvt5I79wficMFgaqEQK'
    pinkerton_urn = 'spotify:album:04xe676vyiTeYNXw15o9jT'
    weezer_urn = 'spotify:artist:3jOstUTkEu2JkjvRdBA5Gu'
    pablo_honey_urn = 'spotify:album:6AZv3m27uyRxi8KyJSfUxL'
    radiohead_urn = 'spotify:artist:4Z8W4fKeB5YxbusRsdQVPb'
    angeles_haydn_urn = 'spotify:album:1vAbqAeuJVWNAe7UR00bdM'
    heavyweight_urn = 'spotify:show:5c26B28vZMN8PG0Nppmn5G'
    heavyweight_id = '5c26B28vZMN8PG0Nppmn5G'
    heavyweight_url = 'https://open.spotify.com/show/5c26B28vZMN8PG0Nppmn5G'
    reply_all_urn = 'spotify:show:7gozmLqbcbr6PScMjc0Zl4'
    heavyweight_ep1_urn = 'spotify:episode:68kq3bNz6hEuq8NtdfwERG'
    heavyweight_ep1_id = '68kq3bNz6hEuq8NtdfwERG'
    heavyweight_ep1_url = 'https://open.spotify.com/episode/68kq3bNz6hEuq8NtdfwERG'
    reply_all_ep1_urn = 'spotify:episode:1KHjbpnmNpFmNTczQmTZlR'

    @classmethod
    def setUpClass(self):
        self.spotify = Spotify(
            auth_manager=SpotifyClientCredentials()
        )
        self.spotify.trace = False

    def test_audio_analysis(self):
        result = self.spotify.audio_analysis(self.four_tracks[0])
        typecheck_response(result, self.spotify.audio_analysis)

    def test_audio_features(self):
        results = self.spotify.audio_features(self.four_tracks)
        typecheck_response(results, self.spotify.audio_features)

    def test_recommendations(self):
        results = self.spotify.recommendations(
            seed_tracks=self.four_tracks,
            min_danceability=0,
            max_loudness=0,
            target_popularity=50)
        typecheck_response(results, self.spotify.recommendations)

    def test_artist_urn(self):
        artist = self.spotify.artist(self.radiohead_urn)
        typecheck_response(artist, self.spotify.artist)

    def test_artists(self):
        results = self.spotify.artists([self.weezer_urn, self.radiohead_urn])
        typecheck_response(results, self.spotify.artists)
