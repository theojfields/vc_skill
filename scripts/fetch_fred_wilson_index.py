#!/usr/bin/env python3
import argparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (OpenClaw vc-essay-archive)"}
BASE = "https://avc.com/author/fred8784/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=120)
    args = parser.parse_args()

    url = BASE
    visited = set()
    rows = []
    pages = 0

    while url and url not in visited and pages < args.max_pages:
        visited.add(url)
        pages += 1
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200:
            break
        soup = BeautifulSoup(r.text, "lxml")

        for art in soup.find_all("article"):
            h = art.find(["h1", "h2", "h3"])
            a = h.find("a", href=True) if h else None
            if not a:
                continue
            title = " ".join(a.get_text(" ", strip=True).split())
            link = a["href"]
            t = art.find("time")
            date = (t.get("datetime") or "").split("T")[0] if t else ""
            if title and link:
                rows.append((title, link, date))

        older = None
        for a in soup.find_all("a", href=True):
            txt = " ".join(a.get_text(" ", strip=True).lower().split())
            if txt in ("older posts", "older"):
                older = a["href"]
                break
        url = older

    seen = set()
    dedup = []
    for t, u, d in rows:
        if u in seen:
            continue
        seen.add(u)
        dedup.append((t, u, d))

    out = Path(__file__).resolve().parents[1] / "references" / "fred_wilson_index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("# Fred Wilson (AVC) Post Index\n\n")
        f.write(f"Source: {BASE}\n\n")
        f.write(f"Pages crawled: {pages}\n\n")
        for i, (t, u, d) in enumerate(dedup, 1):
            prefix = f"{d} — " if d else ""
            f.write(f"{i}. {prefix}[{t}]({u})\n")

    print(f"Wrote {out} ({len(dedup)} entries; pages={pages})")


if __name__ == "__main__":
    main()
