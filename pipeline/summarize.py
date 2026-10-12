"""Extractive fallback today, LLM upgrade when keys exist. Always attributes source."""
from __future__ import annotations
import os, re

DISCLAIMER = "Training aid only. Verify against ICAO Annex, AIP and operator manuals."

def _extractive(item):
    s = item.get("summary") or item.get("title")
    sents = re.split(r"(?<=[.!?])\s+", s)
    return " ".join(sents[:2])[:280]

def summarize_llm(items, provider):
    import requests
    texts = "\n".join(f"- {i['title']} ({i['source']}): {i.get('summary','')[:200]}" for i in items[:8])
    prompt = ("Write a 220-word aviation risk morning briefing from these items. "
              "3 bullets: top risks, what changed, action for ARFF/ground ops. "
              "Plain language, no hype, end with disclaimer. Items:\n" + texts)
    if provider == "groq":
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    raise RuntimeError("unsupported provider " + provider)

def build_brief(items):
    provider = os.getenv("LLM_PROVIDER", "none").lower()
    story = None
    if provider in ("groq",) and os.getenv("GROQ_API_KEY"):
        try:
            story = summarize_llm(items, provider)
        except Exception as e:
            story = None
    if not story:
        top = items[:5] if items else []
        lines = [f"{n+1}. {t['title']} — {t['source']}" for n, t in enumerate(top)]
        detail = " ".join(_extractive(t) for t in top[:3])
        story = ("AM Risk morning briefing. Top signals:\n" + ("\n".join(lines) or "No fresh items in lookback window. Standing procedures apply.")
                 + f"\n\nWhat it means: {detail or 'No change to ARFF posture.'}"
                 + f"\nAction: brief marshalling discipline and lead-distance on stands. {DISCLAIMER}")
    # presenter script ~45-60s per 130 words; cap for short-form
    script = ("Good morning from AM Risk. I am your ASI presenter. " + story.strip())[:1200]
    return {"story": story.strip(), "script": script, "disclaimer": DISCLAIMER,
            "items": items, "provider": provider if story else "extractive"}
