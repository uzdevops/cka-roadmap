#!/usr/bin/env python3
"""Normalise ASCII apostrophes to U+2019 in Uzbek prose, leaving code alone.

usage: uznorm.py <file.md> [...]

Prose only: lines inside ``` fences are untouched, and inline `code spans`
are untouched, because a command's quoting must stay byte-identical.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CURLY = "’"


def normalise(text: str) -> tuple[str, int]:
    out, inside, changed = [], False, 0
    for line in text.split("\n"):
        if line.startswith("```"):
            inside = not inside
            out.append(line)
            continue
        if inside:
            out.append(line)
            continue
        # split on inline code spans and convert only the prose parts
        parts = re.split(r"(`[^`]*`)", line)
        for i, part in enumerate(parts):
            if part.startswith("`"):
                continue
            n = part.count("'")
            if n:
                changed += n
                parts[i] = part.replace("'", CURLY)
        out.append("".join(parts))
    return "\n".join(out), changed


def main() -> int:
    for arg in sys.argv[1:]:
        p = Path(arg)
        text = p.read_text(encoding="utf-8")
        new, n = normalise(text)
        if n:
            p.write_text(new, encoding="utf-8")
        print(f"{n:4} apostrophes  {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
