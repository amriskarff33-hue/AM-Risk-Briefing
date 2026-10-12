import pytest
from pipeline.summarize import build_brief

def test_build_brief_extractive():
    items = [
        {"title": "Test incident", "source": "TestFeed", "link": "https://example.com/1",
         "summary": "A test summary.", "published": "2026-10-12T00:00:00+00:00", "score": 1},
    ]
    result = build_brief(items)
    assert "story" in result
    assert "script" in result
    assert "disclaimer" in result
    assert result["provider"] == "extractive"
    assert "Test incident" in result["story"]

def test_build_brief_empty():
    result = build_brief([])
    assert "story" in result
    assert "No fresh items" in result["story"]

def test_build_brief_script_starts_with_greeting():
    items = [{"title": "X", "source": "Y", "link": "https://x.com", "summary": "Z",
              "published": "2026-10-12T00:00:00+00:00", "score": 0}]
    result = build_brief(items)
    assert result["script"].startswith("Good morning from AM Risk")
