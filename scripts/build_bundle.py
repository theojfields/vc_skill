#!/usr/bin/env python3
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--author", choices=["paul", "fred"], required=True)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    src = skill_dir / "cache" / args.author
    files = sorted(src.glob("*.md"), key=lambda x: x.name)

    selected = files[: args.limit]
    out = Path(args.out)
    if not out.is_absolute():
        out = skill_dir / out
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        f.write(f"# {args.author.title()} Bundle\n\n")
        f.write(f"Included essays/posts: {len(selected)}\n\n")
        for i, fp in enumerate(selected, 1):
            f.write(f"\n\n---\n\n## {i}. {fp.stem}\n\n")
            f.write(fp.read_text(encoding="utf-8", errors="ignore"))
            f.write("\n")

    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
