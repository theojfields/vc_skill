#!/usr/bin/env python3
import argparse
import hashlib
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (OpenClaw vc-essay-archive)"}


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:100] or "essay"


def extract_text(url: str):
    r = requests.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

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

    # cleanup repeated blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return title, text


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
