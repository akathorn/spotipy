# -*- coding: utf-8 -*-

import os
import unittest
from typing import Any

from spotipy import CLIENT_CREDS_ENV_VARS as CCEV
from spotipy import (CacheFileHandler, Spotify, SpotifyClientCredentials,
                     SpotifyException, SpotifyOAuth, SpotifyPKCE, json_types)
from tests import helpers
from tests.typechecker import TypeChecker


def _make_spotify(scopes=None, retries=None):

    retries = retries or Spotify.max_retries

    auth_manager = SpotifyOAuth(
        scope=scopes,
        cache_handler=CacheFileHandler()
    )

    spotify = Spotify(
        auth_manager=auth_manager,
        retries=retries
    )

    return spotify


class SpotipyNonUserEndpointTypes(unittest.TestCase):
    """
    These tests require client authentication - provide client credentials
    using the following environment variables

    ::

        'SPOTIPY_CLIENT_ID'
        'SPOTIPY_CLIENT_SECRET'
    """

    four_tracks = ["spotify:track:6RtPijgfPKROxEzTHNRiDp",
                   "spotify:track:7IHOIqZUUInxjVkko181PB",
                   "4VrWlk8IQxevMvERoX08iC",
                   "http://open.spotify.com/track/3cySlItpiPiIAzU3NyHCJf"]

    creep_urn = 'spotify:track:6b2oQwSGFkzsMtQruIWm2p'
    el_scorcho_urn = 'spotify:track:0Svkvt5I79wficMFgaqEQJ'
    pinkerton_urn = 'spotify:album:04xe676vyiTeYNXw15o9jT'
    weezer_urn = 'spotify:artist:3jOstUTkEu2JkjvRdBA5Gu'
    pablo_honey_urn = 'spotify:album:6AZv3m27uyRxi8KyJSfUxL'
    radiohead_urn = 'spotify:artist:4Z8W4fKeB5YxbusRsdQVPb'
    heavyweight_urn = 'spotify:show:5c26B28vZMN8PG0Nppmn5G'
    reply_all_urn = 'spotify:show:7gozmLqbcbr6PScMjc0Zl4'
    heavyweight_ep1_urn = 'spotify:episode:68kq3bNz6hEuq8NtdfwERG'
    reply_all_ep1_urn = 'spotify:episode:1KHjbpnmNpFmNTczQmTZlR'

    @classmethod
    def setUpClass(cls):
        cls.spotify = Spotify(
            auth_manager=SpotifyClientCredentials()
        )
        cls.spotify.trace = False

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_audio_analysis(self):
        result = self.spotify.audio_analysis(self.four_tracks[0])
        self.assertType(result, self.spotify.audio_analysis)

    def test_audio_features(self):
        results = self.spotify.audio_features(self.four_tracks)
        self.assertType(results, self.spotify.audio_features)

    def test_recommendations(self):
        results = self.spotify.recommendations(
            seed_tracks=self.four_tracks,
            min_danceability=0,
            max_loudness=0,
            target_popularity=50)
        self.assertType(results, self.spotify.recommendations)

    def test_artist_urn(self):
        artist = self.spotify.artist(self.radiohead_urn)
        self.assertType(artist, self.spotify.artist)

    def test_artists(self):
        results = self.spotify.artists([self.weezer_urn, self.radiohead_urn])
        self.assertType(results, self.spotify.artists)

    def test_album_urn(self):
        album = self.spotify.album(self.pinkerton_urn)
        self.assertType(album, self.spotify.album)

    def test_album_tracks(self):
        results = self.spotify.album_tracks(self.pinkerton_urn)
        self.assertType(results, self.spotify.album_tracks)

    def test_albums(self):
        results = self.spotify.albums([self.pinkerton_urn, self.pablo_honey_urn])
        self.assertType(results, self.spotify.albums)

    def test_track_urn(self):
        track = self.spotify.track(self.creep_urn)
        self.assertType(track, self.spotify.track)

    def test_tracks(self):
        results = self.spotify.tracks([self.creep_urn, self.el_scorcho_urn])
        self.assertType(results, self.spotify.tracks)

    def test_artist_top_tracks(self):
        results = self.spotify.artist_top_tracks(self.weezer_urn)
        self.assertType(results, self.spotify.artist_top_tracks)

    def test_artist_related_artists(self):
        results = self.spotify.artist_related_artists(self.weezer_urn)
        self.assertType(results, self.spotify.artist_related_artists)

    def test_artist_search(self):
        results = self.spotify.search(q='weezer', type='artist')
        self.assertType(results, self.spotify.search)

    def test_artist_search_with_market(self):
        results = self.spotify.search(q='weezer', type='artist', market='GB')
        self.assertType(results, self.spotify.search)

    def test_artist_albums(self):
        results = self.spotify.artist_albums(self.weezer_urn)
        self.assertType(results, self.spotify.artist_albums)

    def test_album_search(self):
        results = self.spotify.search(q='weezer pinkerton', type='album')
        self.assertType(results, self.spotify.search)

    def test_track_search(self):
        results = self.spotify.search(q='el scorcho weezer', type='track')
        self.assertType(results, self.spotify.search)

    def test_user(self):
        user = self.spotify.user(user='plamere')
        self.assertType(user, self.spotify.user)

    def test_show_urn(self):
        show = self.spotify.show(self.heavyweight_urn, market="US")
        self.assertType(show, self.spotify.show)

    def test_shows(self):
        results = self.spotify.shows([self.heavyweight_urn, self.reply_all_urn], market="US")
        self.assertType(results, self.spotify.shows)

    def test_show_episodes(self):
        results = self.spotify.show_episodes(self.heavyweight_urn, market="US")
        self.assertType(results, self.spotify.show_episodes)

    def test_episode_urn(self):
        episode = self.spotify.episode(self.heavyweight_ep1_urn, market="US")
        self.assertType(episode, self.spotify.episode)

    def test_episodes(self):
        results = self.spotify.episodes(
            [self.heavyweight_ep1_urn, self.reply_all_ep1_urn],
            market="US"
        )
        self.assertType(results, self.spotify.episodes)

    def test_available_markets(self):
        markets = self.spotify.available_markets()
        self.assertType(markets, self.spotify.available_markets)


class SpotipyPlaylistApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.four_tracks = ["spotify:track:6RtPijgfPKROxEzTHNRiDp",
                           "spotify:track:7IHOIqZUUInxjVkko181PB",
                           "4VrWlk8IQxevMvERoX08iC",
                           "http://open.spotify.com/track/3cySlItpiPiIAzU3NyHCJf"]
        cls.other_tracks = ["spotify:track:2wySlB6vMzCbQrRnNGOYKa",
                            "spotify:track:29xKs5BAHlmlX1u4gzQAbJ",
                            "spotify:track:1PB7gRWcvefzu7t3LJLUlf"]
        assert CCEV['client_username'] in os.environ
        cls.username: str = os.environ[CCEV['client_username']]

        # be wary here, episodes sometimes go away forever
        # which could cause tests that rely on four_episodes
        # to fail

        cls.four_episodes = [
            "spotify:episode:7f9e73vfXKRqR6uCggK2Xy",
            "spotify:episode:4wA1RLFNOWCJ8iprngXmM0",
            "spotify:episode:32vhLjJjT7m3f9DFCJUCVZ",
            "spotify:episode:7cRcsGYYRUFo1OF3RgRzdx",
        ]

        scope = (
            'playlist-modify-public '
            'user-library-read '
            'user-follow-read '
            'user-library-modify '
            'user-read-private '
            'user-top-read '
            'user-follow-modify '
            'user-read-recently-played '
            'ugc-image-upload '
            'user-read-playback-state'
        )

        cls.spotify = _make_spotify(scopes=scope)
        cls.spotify_no_retry = _make_spotify(scopes=scope, retries=0)

        cls.new_playlist_name = 'spotipy-playlist-test'
        cls.new_playlist = helpers.get_spotify_playlist(
            cls.spotify, cls.new_playlist_name, cls.username) or \
            cls.spotify.user_playlist_create(cls.username, cls.new_playlist_name)
        cls.new_playlist_uri = cls.new_playlist['uri']

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_user_playlists(self):
        playlists = self.spotify.user_playlists(self.username, limit=5)
        self.assertType(playlists, self.spotify.user_playlists)

    def test_current_user_playlists(self):
        playlists = self.spotify.current_user_playlists(limit=10)
        self.assertType(playlists, self.spotify.current_user_playlists)

    def test_playlist_is_following(self):
        playlist_to_follow_id = '4erXB04MxwRAVqcUEpu30O'
        follows = self.spotify.playlist_is_following(playlist_to_follow_id, [self.username])
        self.assertType(follows, self.spotify.playlist_is_following)

    def test_playlist_replace_items(self):
        # add tracks to playlist
        snapshot = self.spotify.playlist_add_items(self.new_playlist['id'], self.four_tracks)
        self.assertType(snapshot, self.spotify.playlist_add_items)

        # replace with 3 other tracks
        snapshot = self.spotify.playlist_replace_items(self.new_playlist['id'], self.other_tracks)
        self.assertType(snapshot, self.spotify.playlist_replace_items)

        snapshot = self.spotify.playlist_remove_all_occurrences_of_items(self.new_playlist['id'],
                                                                         self.other_tracks)
        self.assertType(snapshot, self.spotify.playlist_remove_all_occurrences_of_items)

    def test_playlist(self):
        pl = self.spotify.playlist(self.new_playlist['id'])
        self.assertType(pl, self.spotify.playlist)

    def test_playlist_add_items(self):
        # add tracks to playlist
        snapshot = self.spotify.playlist_add_items(self.new_playlist['id'], self.other_tracks)
        self.assertType(snapshot, self.spotify.playlist_add_items)

        snapshot = self.spotify.playlist_remove_all_occurrences_of_items(
            self.new_playlist['id'], self.other_tracks)
        self.assertType(snapshot, self.spotify.playlist_remove_all_occurrences_of_items)

    def test_playlist_cover_image(self):
        # From https://dog.ceo/api/breeds/image/random
        small_image = "https://images.dog.ceo/breeds/poodle-toy/n02113624_8936.jpg"
        dog_base64 = helpers.get_as_base64(small_image)
        self.spotify.playlist_upload_cover_image(self.new_playlist_uri, dog_base64)

        res = self.spotify.playlist_cover_image(self.new_playlist_uri)
        self.assertType(res, self.spotify.playlist_cover_image)


class SpotipyLibraryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.four_tracks = ["spotify:track:6RtPijgfPKROxEzTHNRiDp",
                           "spotify:track:7IHOIqZUUInxjVkko181PB",
                           "4VrWlk8IQxevMvERoX08iC",
                           "http://open.spotify.com/track/3cySlItpiPiIAzU3NyHCJf"]
        cls.album_ids = ["spotify:album:6kL09DaURb7rAoqqaA51KU",
                         "spotify:album:6RTzC0rDbvagTSJLlY7AKl"]
        cls.episode_ids = [
            "spotify:episode:3OEdPEYB69pfXoBrhvQYeC",
            "spotify:episode:5LEFdZ9pYh99wSz7Go2D0g"
        ]
        cls.username = os.getenv(CCEV['client_username'])

        scope = (
            'playlist-modify-public '
            'user-library-read '
            'user-follow-read '
            'user-library-modify '
            'user-read-private '
            'user-top-read '
            'user-follow-modify '
            'user-read-recently-played '
            'ugc-image-upload '
            'user-read-playback-state'
        )
        cls.spotify = _make_spotify(scopes=scope)

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_current_user_saved_tracks(self):
        # TODO make this not fail if someone doesnthave saved tracks
        tracks = self.spotify.current_user_saved_tracks()
        self.assertType(tracks, self.spotify.current_user_saved_tracks)

    def test_current_user_saved_albums(self):
        # Add
        self.spotify.current_user_saved_albums_add(self.album_ids)

        albums = self.spotify.current_user_saved_albums()
        self.assertType(albums, self.spotify.current_user_saved_albums)

        resp = self.spotify.current_user_saved_albums_contains(self.album_ids)
        self.assertType(resp, self.spotify.current_user_saved_albums_contains)

        # Remove
        self.spotify.current_user_saved_albums_delete(self.album_ids)

    def test_current_user_saved_episodes(self):
        # Add
        self.spotify.current_user_saved_episodes_add(self.episode_ids)
        episodes = self.spotify.current_user_saved_episodes(market="US")
        self.assertType(episodes, self.spotify.current_user_saved_episodes)

        # Contains
        resp = self.spotify.current_user_saved_episodes_contains(self.episode_ids)
        self.assertEqual(resp, self.spotify.current_user_saved_episodes_contains)

        # Remove
        self.spotify.current_user_saved_episodes_delete(self.episode_ids)


class SpotipyUserApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.username: str = os.getenv(CCEV['client_username'])

        scope = (
            'playlist-modify-public '
            'user-library-read '
            'user-follow-read '
            'user-library-modify '
            'user-read-private '
            'user-top-read '
            'user-follow-modify '
            'user-read-recently-played '
            'ugc-image-upload '
            'user-read-playback-state'
        )

        cls.spotify = _make_spotify(scopes=scope)

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_basic_user_profile(self):
        user = self.spotify.user(self.username)
        self.assertType(user, self.spotify.user)

    def test_current_user(self):
        user = self.spotify.current_user()
        self.assertType(user, self.spotify.current_user)

    def test_me(self):
        user = self.spotify.me()
        self.assertType(user, self.spotify.me)

    def test_current_user_top_tracks(self):
        response = self.spotify.current_user_top_tracks()
        self.assertType(response, self.spotify.current_user_top_tracks)

    def test_current_user_top_artists(self):
        response = self.spotify.current_user_top_artists()
        self.assertType(response, self.spotify.current_user_top_artists)


class SpotipyBrowseApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spotify = _make_spotify()

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_category(self):
        response = self.spotify.category('rock')
        self.assertType(response, self.spotify.category)

    def test_categories(self):
        response = self.spotify.categories()
        self.assertType(response, self.spotify.categories)

    def test_category_playlists(self):
        response = self.spotify.categories()
        category = 'rock'
        for cat in response['categories']['items']:
            cat_id = cat['id']
            if cat_id == category:
                response = self.spotify.category_playlists(category_id=cat_id)
                self.assertType(response, self.spotify.category_playlists)

    def test_new_releases(self):
        response = self.spotify.new_releases()
        self.assertType(response, self.spotify.new_releases)

    def test_featured_releases(self):
        response = self.spotify.featured_playlists()
        self.assertType(response, self.spotify.featured_playlists)


class SpotipyFollowApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.username = os.getenv(CCEV['client_username'])

        scope = (
            'playlist-modify-public '
            'user-library-read '
            'user-follow-read '
            'user-library-modify '
            'user-read-private '
            'user-top-read '
            'user-follow-modify '
            'user-read-recently-played '
            'ugc-image-upload '
            'user-read-playback-state'
        )

        cls.spotify = _make_spotify(scopes=scope)

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_current_user_follows(self):
        response = self.spotify.current_user_followed_artists()
        self.assertType(response, self.spotify.current_user_followed_artists)


class SpotipyPlayerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.username = os.getenv(CCEV['client_username'])

        scope = (
            'playlist-modify-public '
            'user-library-read '
            'user-follow-read '
            'user-library-modify '
            'user-read-private '
            'user-top-read '
            'user-follow-modify '
            'user-read-recently-played '
            'ugc-image-upload '
            'user-read-playback-state'
        )

        cls.spotify = _make_spotify(scopes=scope)

    def assertType(self, value: Any, function: Any) -> None:
        typechecker = TypeChecker()
        result = typechecker.compare_with_signature(value, function)
        self.assertFalse(result.has_errors, msg="Type mismatch\n" + result.pprint())

    def test_devices(self):
        # No devices playing by default
        res = self.spotify.devices()
        self.assertType(res, self.spotify.devices)

    def test_current_user_recently_played(self):
        # No cursor
        res = self.spotify.current_user_recently_played()
        self.assertType(res, self.spotify.current_user_recently_played)
