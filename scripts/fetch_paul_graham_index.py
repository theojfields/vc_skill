#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (OpenClaw vc-essay-archive)"}
BASE = "https://paulgraham.com/articles.html"


def main():
    html = requests.get(BASE, headers=UA, timeout=30).text
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = " ".join(a.get_text(" ", strip=True).split())
        if not title:
            continue
        if href.endswith(".html") and href not in ("index.html", "articles.html"):
            rows.append((title, urljoin(BASE, href)))

    seen = set()
    dedup = []
    for t, u in rows:
        if u in seen:
            continue
        seen.add(u)
        dedup.append((t, u))

    out = Path(__file__).resolve().parents[1] / "references" / "paul_graham_index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("# Paul Graham Essay Index\n\n")
        f.write(f"Source: {BASE}\n\n")
        for i, (t, u) in enumerate(dedup, 1):
            f.write(f"{i}. [{t}]({u})\n")

    print(f"Wrote {out} ({len(dedup)} entries)")


if __name__ == "__main__":
    main()
