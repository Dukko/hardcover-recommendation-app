from app.hardcover_client import parse_library_response

SAMPLE_RESPONSE = {
    "data": {
        "me": [
            {
                "user_books": [
                    {
                        "rating": 4,
                        "book": {
                            "title": "Dracula",
                            "release_date": "1897-05-26",
                            "rating": 4.2,
                            "taggings": [{"tag": {"tag": "Gothic"}}, {"tag": {"tag": "Horror"}}],
                            "contributions": [{"author": {"name": "Bram Stoker"}}],
                        },
                    },
                    {
                        # no tags, no author, no release date -- should still parse
                        "rating": 0,
                        "book": {
                            "title": "Untitled",
                            "release_date": "",
                            "rating": None,
                            "taggings": [],
                            "contributions": [],
                        },
                    },
                ]
            }
        ]
    }
}


def test_parse_library_response_extracts_fields():
    library = parse_library_response(SAMPLE_RESPONSE)
    assert len(library) == 2

    dracula = library[0]
    assert dracula["title"] == "Dracula"
    assert dracula["author"] == "Bram Stoker"
    assert dracula["year"] == "1897"
    assert dracula["tags"] == "Gothic, Horror"
    assert dracula["full_str"] == "Dracula by Bram Stoker (1897)"


def test_parse_library_response_handles_missing_data():
    untitled = parse_library_response(SAMPLE_RESPONSE)[1]
    assert untitled["author"] == "Unknown"
    assert untitled["year"] == "Unknown"
    assert untitled["tags"] == "Untagged"


def test_parse_library_response_empty():
    empty = {"data": {"me": [{"user_books": []}]}}
    assert parse_library_response(empty) == []
