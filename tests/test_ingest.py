import pytest
from pipeline.ingest import fetch

def test_fetch_returns_items():
    cfg = {
        "feeds": ["https://simpleflying.com/feed/"],
        "keywords": ["aviation", "airport", "safety"],
        "lookback_hours": 720,
        "max_items": 5,
    }
    items = fetch(cfg)
    assert isinstance(items, list)
    assert len(items) > 0
    for item in items:
        assert "title" in item
        assert "link" in item
        assert "source" in item

def test_fetch_dedup():
    cfg = {
        "feeds": ["https://simpleflying.com/feed/", "https://simpleflying.com/feed/"],
        "keywords": [],
        "lookback_hours": 720,
        "max_items": 10,
    }
    items = fetch(cfg)
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids))

def test_fetch_respects_max():
    cfg = {
        "feeds": ["https://www.aerotime.aero/feed"],
        "keywords": [],
        "lookback_hours": 720,
        "max_items": 3,
    }
    items = fetch(cfg)
    assert len(items) <= 3
