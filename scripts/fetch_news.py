#!/usr/bin/env python3
"""
Fetches recent AI news from public RSS feeds, then uses the Claude API to pick
3 diverse, business-relevant items and write French headline/summary/source
for each, matching the Sana Consulting "Veille AI" carousel format.

Usage:
    python3 fetch_news.py --out content.json
    python3 fetch_news.py            # prints JSON to stdout

Requires env var ANTHROPIC_API_KEY. Optional env var ANTHROPIC_MODEL to
override the default model (check console.anthropic.com for the current
recommended model id if the default below has been retired).
"""
import datetime
import json
import os
import sys
import zoneinfo

import anthropic
import feedparser

FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://www.technologyreview.com/feed/",
]

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


def collect_candidates(max_per_feed=5):
    items = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"WARN: failed to parse {url}: {e}", file=sys.stderr)
            continue
        source = feed.feed.get("title", url) if hasattr(feed, "feed") else url
        for entry in feed.entries[:max_per_feed]:
            title = (entry.get("title") or "").strip()
            summary = (entry.get("summary") or entry.get("description") or "").strip()
            link = entry.get("link", "")
            if title:
                items.append({"title": title, "summary": summary, "link": link, "source": source})
    return items


def french_date_today():
    tz = zoneinfo.ZoneInfo("America/Toronto")
    now = datetime.datetime.now(tz)
    mois = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    return f"{now.day} {mois[now.month - 1]} {now.year}"


def build_prompt(candidates):
    listing = "\n".join(
        f"{i + 1}. [{c['source']}] {c['title']} — {c['summary'][:300]}"
        for i, c in enumerate(candidates)
    )
    return f"""Voici une liste d'actualités récentes en intelligence artificielle (en anglais, issues de flux RSS) :

{listing}

Choisis les 3 actualités les PLUS pertinentes, récentes et diversifiées (évite 3 news sur le même sujet ; vise un mélange parmi : lancements/produits, régulation/gouvernance, financement/business, recherche) pour un public d'affaires/consulting francophone.

Pour CHACUNE des 3 actualités choisies, rédige en français :
- "headline": un titre court et percutant, maximum 90 caractères
- "summary": un résumé de 1 à 2 phrases, maximum 180 caractères
- "source": le nom de la source (ex: TechCrunch, VentureBeat)

Réponds UNIQUEMENT avec un objet JSON valide de cette forme, sans aucun texte avant ou après :
{{
  "news": [
    {{"headline": "...", "summary": "...", "source": "..."}},
    {{"headline": "...", "summary": "...", "source": "..."}},
    {{"headline": "...", "summary": "...", "source": "..."}}
  ],
  "recap": ["phrase courte 1", "phrase courte 2", "phrase courte 3"]
}}
"""


def main():
    candidates = collect_candidates()
    if len(candidates) < 3:
        print("ERROR: not enough news candidates found from RSS feeds", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    prompt = build_prompt(candidates)
    resp = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if hasattr(block, "text")).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    data = json.loads(text)
    data["date_fr"] = french_date_today()

    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path}", file=sys.stderr)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
