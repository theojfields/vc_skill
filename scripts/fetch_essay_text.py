#!/usr/bin/env python3
import argparse
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (OpenClaw vc-essay-archive)"}
ALLOWED_HOSTS = {"paulgraham.com", "www.paulgraham.com", "avc.com", "www.avc.com", "avc.xyz", "www.avc.xyz"}
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5MB safety cap


def slugify(s: str) -> str:
    # Intentional defensive filename normalization (not incidental)
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:100] or "essay"


def sanitize_text(text: str) -> str:
    # Keep printable text + common whitespace; strip control chars
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def validate_allowed_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only https:// URLs are allowed")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host not allowed: {host}")


def get_limited_text(url: str, timeout: int = 40) -> str:
    with requests.get(url, headers=UA, timeout=timeout, stream=True, verify=True, allow_redirects=True) as r:
        r.raise_for_status()

        # Validate redirect target as well
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

        # Prefer declared encoding, fallback utf-8
        encoding = r.encoding or "utf-8"
        return data.decode(encoding, errors="replace")


def extract_text(url: str):
    validate_allowed_url(url)
    html = get_limited_text(url)
    soup = BeautifulSoup(html, "lxml")

    title = ""
    if soup.title:
        title = " ".join(soup.title.get_text(" ", strip=True).split())

    # Prefer semantic article container
    article = soup.find("article")
    if article:
        text = article.get_text("\n", strip=True)
    else:
        # fallback: body text
        body = soup.find("body")
        text = body.get_text("\n", strip=True) if body else soup.get_text("\n", strip=True)

    return sanitize_text(title), sanitize_text(text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--author", choices=["paul", "fred"], required=True)
    args = p.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    out_dir = skill_dir / "cache" / args.author
    out_dir.mkdir(parents=True, exist_ok=True)

    title, text = extract_text(args.url)
    key = hashlib.sha1(args.url.encode()).hexdigest()[:10]
    name = slugify(title) if title else "essay"
    out = out_dir / f"{name}-{key}.md"

    with out.open("w", encoding="utf-8") as f:
        f.write(f"# {title or 'Untitled'}\n\n")
        f.write(f"Source: {args.url}\n\n")
        f.write(text)
        f.write("\n")

    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
