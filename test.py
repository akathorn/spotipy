import spotipy
from spotipy.json_types import Album, SimplifiedTrack
from spotipy.util import prompt_for_user_token

# Everything typechecks in strict mode except this line
sp = spotipy.client.Spotify(auth=prompt_for_user_token("akathorn"))


def first_track(album: Album) -> SimplifiedTrack:
    tracks = album["tracks"]  # Type is Page[SimplifiedTrack]
    track = tracks["items"][0]  # Type is SimplifiedTrack
    return track


album = sp.album("7JuNfn3ORPPhYvELaud5iH?si=fLrF1f7STv6r-9keG1_Oaw")  # Type is Album
name = first_track(album)["name"]
print(name)


# At runtime they are just dicts
assert isinstance(album, dict)
assert isinstance(first_track(album), dict)

for k, v in album.items():
    # k has type str and v has type Any
    print(k.upper())
