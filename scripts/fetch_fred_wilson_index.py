#!/usr/bin/env python3
import argparse
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (OpenClaw vc-essay-archive)"}
BASE = "https://avc.com/author/fred8784/"
ALLOWED_HOSTS = {"avc.com", "www.avc.com"}


def get_limited_html(url: str, max_response_bytes: int) -> str:
    with requests.get(url, headers=UA, timeout=30, stream=True, verify=True, allow_redirects=True) as r:
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}")

        final_host = (urlparse(r.url).hostname or "").lower()
        if final_host not in ALLOWED_HOSTS:
            raise ValueError(f"Redirected to non-allowed host: {final_host}")

        content_length = r.headers.get("Content-Length")
        if content_length and int(content_length) > max_response_bytes:
            raise ValueError(f"Response too large: {content_length} bytes")

        data = bytearray()
        for chunk in r.iter_content(chunk_size=16384):
            if not chunk:
                continue
            data.extend(chunk)
            if len(data) > max_response_bytes:
                raise ValueError(f"Response exceeded max size ({max_response_bytes} bytes)")

        return data.decode(r.encoding or "utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--max-response-bytes", type=int, default=2 * 1024 * 1024)  # 2MB/page
    parser.add_argument("--total-byte-budget", type=int, default=25 * 1024 * 1024)  # 25MB run cap
    args = parser.parse_args()

    url = BASE
    visited = set()
    rows = []
    pages = 0
    bytes_used = 0

    while url and url not in visited and pages < args.max_pages:
        visited.add(url)
        pages += 1

        try:
            html = get_limited_html(url, args.max_response_bytes)
        except Exception as e:
            print(f"Stopping at page {pages} ({url}): {e}")
            break

        bytes_used += len(html.encode("utf-8", errors="ignore"))
        if bytes_used > args.total_byte_budget:
            print(f"Stopping: total byte budget exceeded ({args.total_byte_budget})")
            break

        soup = BeautifulSoup(html, "lxml")

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
        f.write(f"Pages crawled: {pages}\n")
        f.write(f"Bytes processed: {bytes_used}\n\n")
        for i, (t, u, d) in enumerate(dedup, 1):
            prefix = f"{d} — " if d else ""
            f.write(f"{i}. {prefix}[{t}]({u})\n")

    print(f"Wrote {out} ({len(dedup)} entries; pages={pages}; bytes={bytes_used})")


if __name__ == "__main__":
    main()
