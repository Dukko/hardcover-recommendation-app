import pytest

from app.recommend import build_prompt, parse_recommendations

FILTERS = {
    "moods": "Eerie, Dark",
    "genres": "Gothic Horror",
    "pages": 400,
    "year_range": (1897, 2026),
    "min_rating": 3.0,
}

LIBRARY = [
    {"title": "Dracula", "author": "Bram Stoker", "rating": 5, "tags": "Gothic", "full_str": "Dracula by Bram Stoker (1897)"},
]


def test_build_prompt_includes_filters_and_exclusions():
    prompt = build_prompt(LIBRARY, FILTERS)
    assert "Eerie, Dark" in prompt
    assert "Gothic Horror" in prompt
    assert "1897" in prompt
    assert "2026" in prompt
    assert "Dracula" in prompt


def test_build_prompt_without_skew_books_omits_section():
    prompt = build_prompt(LIBRARY, FILTERS)
    assert "SKEW TOWARD" not in prompt


def test_build_prompt_includes_skew_books():
    filters = {**FILTERS, "skew_books": ["The Haunting of Hill House", "House of Leaves"]}
    prompt = build_prompt(LIBRARY, filters)
    assert "SKEW TOWARD" in prompt
    assert "The Haunting of Hill House" in prompt
    assert "House of Leaves" in prompt


def test_parse_recommendations_fenced_json():
    text = '```json\n[{"title": "A", "author": "B", "reason": "C"}]\n```'
    result = parse_recommendations(text)
    assert result == [{"title": "A", "author": "B", "reason": "C"}]


def test_parse_recommendations_bare_array():
    text = 'Here is my answer:\n[{"title": "A", "author": "B", "reason": "C"}]\nEnjoy!'
    result = parse_recommendations(text)
    assert result == [{"title": "A", "author": "B", "reason": "C"}]


def test_parse_recommendations_invalid_raises():
    with pytest.raises(Exception):
        parse_recommendations("not json at all")
