"""RSS-first ingest. No paywall scraping. Dedup by URL hash."""
from __future__ import annotations
import hashlib, re, time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import requests
import yaml

UA = {"User-Agent": "AMRiskBrief/1.0 (+iam-asi; contact ops)"}

def _parse(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code == 200 and r.content:
            return feedparser.parse(r.content)
    except Exception:
        pass
    return feedparser.parse(url)

def load_feeds(path="config/feeds.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def _ts(entry):
    for k in ("published_parsed", "updated_parsed"):
        v = entry.get(k)
        if v:
            return datetime(*v[:6], tzinfo=timezone.utc)
    for k in ("published", "updated"):
        v = entry.get(k)
        if v:
            try:
                return parsedate_to_datetime(v)
            except Exception:
                pass
    return datetime.now(timezone.utc)

def fetch(cfg):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cfg.get("lookback_hours", 30))
    kws = [k.lower() for k in cfg.get("keywords", [])]
    seen, items = set(), []
    for url in cfg.get("feeds", []):
        try:
            d = _parse(url)
        except Exception as e:
            items.append({"source": url, "title": f"Feed error: {e}", "link": url,
                          "published": datetime.now(timezone.utc).isoformat(), "error": True})
            continue
        src = d.feed.get("title", url)
        if d.get("bozo") and not d.entries:
            items.append({"source": url, "title": f"Feed parse warning: {d.get('bozo_exception')}", "link": url,
                          "published": datetime.now(timezone.utc).isoformat(), "error": True})
            continue
        for e in d.entries[:25]:
            link = e.get("link", "")
            h = hashlib.sha256(link.encode()).hexdigest()[:12]
            if h in seen or not link:
                continue
            seen.add(h)
            pub = _ts(e)
            if pub < cutoff:
                continue
            title = re.sub(r"\s+", " ", e.get("title", "Untitled")).strip()
            summary = re.sub(r"<[^>]+>", " ", e.get("summary", "") or e.get("description", ""))
            summary = re.sub(r"\s+", " ", summary).strip()[:600]
            score = sum(1 for k in kws if k in (title + " " + summary).lower())
            items.append({"id": h, "source": src, "title": title, "link": link,
                          "published": pub.isoformat(), "summary": summary, "score": score})
    items.sort(key=lambda x: (-x.get("score", 0), x.get("published", "")), reverse=False)
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return items[: cfg.get("max_items", 12)]
