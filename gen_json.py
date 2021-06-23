import urllib.request

from bs4 import BeautifulSoup

url = "https://developer.spotify.com/documentation/web-api/reference/"


def to_python_type(tp: str):
    if "|" in tp:
        # TODO:
        # There are some cases in which there can be either an EpisodeObject or a TrackObject in the
        # same field. We want to ignore EpisodeObjects
        return '"Track"'

    if tp.startswith("Array"):
        inner = tp[len("Array["): -1]
        return f"List[{to_python_type(inner)}]"

    mapping = {
        "String": "str",
        "Integer": "int",
        "Float": "float",
        "Boolean": "bool",
        "Timestamp": "str",
    }

    return mapping.get(tp, f'"{tp.replace("Object", "")}"')


def print_typed_dict(heading):
    name = heading.text.replace("Object", "")
    # Skip paging objects
    if name in ["Paging", "CursorPaging"]:
        return

    table = next(tag for tag in heading.next_siblings if tag.name == "table")
    fields = []
    for field in table.tbody("tr"):
        key, type_ = field("td")
        field_name = key.code.text

        # Hardcoded stuff
        if field_name == "linked_from":
            field_type = '"LinkedTrack"'
        elif name == "Album" and field_name == "tracks":
            field_type = "'Page[SimplifiedTrack]'"
        else:
            field_type = to_python_type(type_.text)

        fields.append(f'"{field_name}": {field_type}')

    if name == "Cursor":
        fields.append(f'"before": str')

    print(f'{name} = TypedDict("{name}", {{')
    for field in fields:
        print(f"\t{field},")
    print("})\n")


# Get the html
fp = urllib.request.urlopen(url)
html = fp.read().decode("utf8")

# Soup
soup = BeautifulSoup(html, "html.parser")

# Get the headings
section_heading, *object_headings = soup(id=lambda id: id and id.startswith("object"))

# Write the types
for h in object_headings:
    print_typed_dict(h)
