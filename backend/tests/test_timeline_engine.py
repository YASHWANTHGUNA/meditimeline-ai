import pytest
from timeline_engine import parse_and_normalize_date, process_timeline_events


@pytest.mark.parametrize("raw,expected", [
    ("2026-10-13", ("2026-10-13", "day")),
    ("13/10/2026", ("2026-10-13", "day")),
    ("March 5, 2024", ("2024-03-05", "day")),
    ("5 Mar 2024", ("2024-03-05", "day")),
    ("Mar 2024", ("2024-03-01", "month")),
    ("2018", ("2018-01-01", "year")),
])
def test_date_formats(raw, expected):
    key, _, precision = parse_and_normalize_date(raw)
    assert (key, precision) == expected


@pytest.mark.parametrize("raw", [None, "", "unknown", "childhood", "31/02/2024", "gibberish"])
def test_undated_or_invalid(raw):
    assert parse_and_normalize_date(raw)[2] == "undated"


def test_sorting_and_undated_bucket_last():
    events = [
        {"title": "c", "date": "2024-05-01"},
        {"title": "undated"},
        {"title": "a", "date": "2018"},
        {"title": "b", "original_date_str": "Mar 2020"},
    ]
    out = process_timeline_events(events)
    assert [e["title"] for e in out["all_events"]] == ["a", "b", "c", "undated"]
    assert out["dated_count"] == 3 and out["undated_count"] == 1 and out["total_events"] == 4


def test_stable_order_for_same_date():
    events = [{"title": str(i), "date": "2024-01-01"} for i in range(5)]
    assert [e["title"] for e in process_timeline_events(events)["all_events"]] == list("01234")