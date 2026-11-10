#!/usr/bin/env python3
"""Fails if the kit mentions a client. Run it before every commit to the kit.

  python dev/leak_check.py --workspace PATH [--workspace PATH ...] [--term WORD ...]

The words come from each named workspace's workspace.yaml: its `client`, and
everything listed under `confidential_terms`. The kit is reusable and may be
public, so nothing from a client's workspace belongs in it. Matching ignores
case. Files inside the built .plugin archives are searched too.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kit" / "hooks"))
import kitlib  # noqa: E402

SKIP_FOLDERS = {".git", "__pycache__"}


def terms_from(workspace: Path) -> list[str]:
    config = workspace / kitlib.CONFIG_NAME
    if not config.is_file():
        raise SystemExit(f"no workspace.yaml in {workspace}")
    raw = kitlib.parse_simple_yaml(config.read_text(encoding="utf-8"))
    terms = [str(raw.get("client") or "")] + kitlib.as_list(raw.get("confidential_terms"))
    return [t.strip() for t in terms if t and t.strip()]


def texts(root: Path):
    """Every readable text in the kit: (label, text)."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or SKIP_FOLDERS & set(path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    try:
                        yield f"{rel}!{name}", archive.read(name).decode("utf-8")
                    except UnicodeDecodeError:
                        pass
            continue
        try:
            yield rel, path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            pass


def find(root: Path, terms: list[str]) -> list[tuple[str, int, str, str]]:
    hits = []
    lowered = [(term, term.lower()) for term in terms]
    for label, text in texts(root):
        for number, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for term, needle in lowered:
                if needle in low:
                    hits.append((label, number, term, line.strip()[:120]))
    return hits


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Fail if the kit mentions a client.")
    parser.add_argument("--workspace", action="append", default=[], help="a client workspace to take words from")
    parser.add_argument("--term", action="append", default=[], help="an extra word to look for")
    parser.add_argument("--kit", default=str(ROOT), help="the kit repository. Default: the one this script is in")
    args = parser.parse_args(argv)

    terms = list(args.term)
    for workspace in args.workspace:
        terms += terms_from(Path(workspace).expanduser().resolve())
    terms = sorted({t for t in terms if t}, key=str.lower)
    if not terms:
        print("Nothing to look for. Name a workspace with --workspace, or a word with --term.")
        return 2

    hits = find(Path(args.kit).resolve(), terms)
    if not hits:
        print(f"Clean: none of {len(terms)} word(s) appear in the kit.")
        return 0
    print(f"{len(hits)} line(s) in the kit mention a client:")
    for label, number, term, line in hits:
        print(f"  {label}:{number}  [{term}]  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
