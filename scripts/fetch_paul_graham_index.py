#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (OpenClaw vc-essay-archive)"}
BASE = "https://paulgraham.com/articles.html"
ALLOWED_HOSTS = {"paulgraham.com", "www.paulgraham.com"}
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB


def get_limited_html(url: str) -> str:
    with requests.get(url, headers=UA, timeout=30, stream=True, verify=True, allow_redirects=True) as r:
        r.raise_for_status()
        final_host = (urlparse(r.url).hostname or "").lower()
        if final_host not in ALLOWED_HOSTS:
            raise ValueError(f"Redirected to non-allowed host: {final_host}")

        content_length = r.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_RESPONSE_BYTES:
            raise ValueError(f"Response too large: {content_length} bytes")

        data = bytearray()
        for chunk in r.iter_content(chunk_size=16384):
            if not chunk:
                continue
            data.extend(chunk)
            if len(data) > MAX_RESPONSE_BYTES:
                raise ValueError(f"Response exceeded max size ({MAX_RESPONSE_BYTES} bytes)")

        return data.decode(r.encoding or "utf-8", errors="replace")


def main():
    html = get_limited_html(BASE)
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
