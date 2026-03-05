#!/usr/bin/env python3
import argparse
from pathlib import Path


def resolve_safe_out_path(skill_dir: Path, out_arg: str) -> Path:
    out = Path(out_arg)
    if not out.is_absolute():
        out = skill_dir / out

    resolved = out.resolve()
    skill_root = skill_dir.resolve()

    # Prevent writes outside the skill directory (agent/prompt-injection safety)
    try:
        resolved.relative_to(skill_root)
    except ValueError as exc:
        raise ValueError(f"--out must stay inside skill directory: {skill_root}") from exc

    if resolved.suffix.lower() != ".md":
        raise ValueError("--out must point to a .md file")

    return resolved


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
    out = resolve_safe_out_path(skill_dir, args.out)
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
