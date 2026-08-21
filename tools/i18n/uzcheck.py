#!/usr/bin/env python3
"""Structural check of an Uzbek lesson translation against its English source.

usage: uzcheck.py <track> [slug ...]      (no slug = every translated lesson)

Checks the things a translator can silently get wrong: a dropped section, a
mangled command, an ASCII apostrophe in prose, a missing Check-yourself.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "backend/app/seed_data/tracks"
FENCE = re.compile(r"^```")


def split_fences(text: str) -> tuple[list[str], list[str]]:
    """Returns (prose lines, code lines) - code = everything inside ``` fences."""
    prose, code, inside = [], [], False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            code.append(line)
            continue
        (code if inside else prose).append(line)
    return prose, code


COMMAND = re.compile(
    r"\b(kubectl|helm|kustomize|docker|podman|systemctl|journalctl|crictl|etcdctl|"
    r"etcdutl|kubeadm|openssl|curl|wget|ssh|scp|rsync|tar|apt|apt-get|dnf|rpm|dpkg|"
    r"nft|iptables|firewall-cmd|ufw|nmcli|netplan|ip|ss|mount|umount|findmnt|lsblk|"
    r"fdisk|parted|mkfs|mkswap|swapon|pvcreate|vgcreate|lvcreate|lvextend|lvreduce|"
    r"useradd|usermod|groupadd|chage|passwd|setfacl|getfacl|chmod|chown|chattr|"
    r"semanage|setsebool|restorecon|getenforce|sysctl|modprobe|virsh|virt-install|"
    r"qemu-img|chronyc|timedatectl|logrotate|crontab|find|grep|sed|awk|nginx)\b"
    # not when it is the head of a hyphenated identifier: "kubeadm-config" is
    # the name of a ConfigMap in a prose line, not an invocation of kubeadm.
    r"(?!-)"
)
YAML_LINE = re.compile(r"^\s*-?\s*[A-Za-z_][A-Za-z0-9_.\-/]*:(\s|$)")
# "1. kubeadm (the tool)   on the control plane node" is an outline, not a
# command, even though it names one - those labels are prose and translatable.
OUTLINE = re.compile(r"^\s*\d+\.\s")
# Drawn arrows only appear in diagrams, never in a shell command.
ARROW = re.compile(r"[→←↔▶◀⟶⟵]")


def code_signature(code: list[str]) -> list[str]:
    """Code lines that must survive translation byte-identical.

    Commands and YAML must never change. ASCII diagrams and prose labels
    inside a fence may be translated, so they are not compared.
    """
    out = []
    for line in code:
        s = line.strip()
        if not s or s.startswith("```") or s.startswith("#") or s.startswith("//"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].rstrip()  # a trailing comment may be translated
            s = line.strip()
        # A bare drawn arrow makes the line a diagram row, not an invocation,
        # so its labels are prose and translatable. An arrow *inside quotes* is
        # part of a command's argument - jsonpath'{" → "} - and stays.
        if not s or OUTLINE.match(line):
            continue
        if ARROW.search(re.sub(r"""(["'])(?:(?!\1).)*\1""", "", line)):
            continue
        if COMMAND.search(s) or YAML_LINE.match(line):
            out.append(line.rstrip())
    return out


def check(track: str, slug: str) -> list[str]:
    en_p = ROOT / track / "lessons" / f"{slug}.md"
    uz_p = ROOT / track / "i18n" / "uz" / "lessons" / f"{slug}.md"
    if not en_p.is_file():
        return [f"no English source: {en_p}"]
    if not uz_p.is_file():
        return ["missing translation"]

    en, uz = en_p.read_text(encoding="utf-8"), uz_p.read_text(encoding="utf-8")
    problems: list[str] = []

    en_prose, en_code = split_fences(en)
    uz_prose, uz_code = split_fences(uz)

    def count(lines: list[str], pattern: str) -> int:
        return sum(1 for line in lines if re.match(pattern, line))

    pairs = [
        ("h2 headings", r"^## ", en_prose, uz_prose),
        ("code fences", r"^```", en.splitlines(), uz.splitlines()),
        ("admonitions", r"^:::", en_prose, uz_prose),
        ("table rows", r"^\s*\|", en_prose, uz_prose),
    ]
    for name, pattern, a, b in pairs:
        na, nb = count(a, pattern), count(b, pattern)
        if na != nb:
            problems.append(f"{name}: en={na} uz={nb}")

    sig_en, sig_uz = code_signature(en_code), code_signature(uz_code)
    if sig_en != sig_uz:
        for i, (a, b) in enumerate(zip(sig_en, sig_uz)):
            if a != b:
                problems.append(f"code differs at line {i + 1}:\n    en: {a}\n    uz: {b}")
                break
        else:
            problems.append(f"code line count: en={len(sig_en)} uz={len(sig_uz)}")

    # ASCII apostrophe in prose (outside inline code) is the house-style error
    for n, line in enumerate(uz_prose, 1):
        stripped = re.sub(r"`[^`]*`", "", line)
        if "'" in stripped:
            problems.append(f"ASCII apostrophe in prose, line ~{n}: {line.strip()[:70]}")
            break

    # "Pod larni" instead of "Pod'larni": the suffix must attach to the noun
    detached = re.compile(
        r"\b([A-Z][A-Za-z]+) (larni|laridagi|larga|larda|lardan|lar|dagi|ning|dan|ni|ga|da)\b"
    )
    # ...and after an inline code span it attaches with U+2019: `man`’dan,
    # never "`man` dan" and never "`man`dan".
    SUF = r"(?:larning|lardan|larga|larda|larni|lar|dagi|ning|gacha|dan|siz|ni|ga|da)"
    # The span may wrap across a line, so this one is matched on whole prose
    # chunks rather than line by line.
    code_suffix = re.compile(r"(`[^`]+`) ?(?<!’)(" + SUF + r")\b")
    inside = False
    for n, line in enumerate(uz.splitlines(), 1):
        if line.startswith("```"):
            inside = not inside
            continue
        if inside:
            continue
        m = detached.search(line)
        if m:
            problems.append(f"detached suffix, line {n}: {m.group(0)}")
            break

    parts = re.split(r"(?m)(^```.*$)", uz)
    inside = False
    for part in parts:
        if part.startswith("```"):
            inside = not inside
            continue
        if inside:
            continue
        m = code_suffix.search(part)
        if m and "`’" not in m.group(0):
            frag = " ".join(m.group(0).split())[:60]
            problems.append(f"suffix not attached to code span: {frag}")
            break

    if "## O’zingizni tekshiring" not in uz:
        problems.append("missing '## O’zingizni tekshiring'")
    else:
        tail = uz.split("## O’zingizni tekshiring", 1)[1]
        n = len(re.findall(r"^\d\.", tail, re.M))
        if n != 3:
            problems.append(f"Check-yourself questions: {n} (want 3)")

    ratio = len(uz) / max(len(en), 1)
    if not 0.75 <= ratio <= 1.75:
        problems.append(f"length ratio {ratio:.2f} (want 0.75-1.75)")

    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    track = sys.argv[1]
    slugs = sys.argv[2:]
    if not slugs:
        d = ROOT / track / "i18n" / "uz" / "lessons"
        slugs = sorted(p.stem for p in d.glob("*.md"))

    bad = 0
    for slug in slugs:
        problems = check(track, slug)
        if problems:
            bad += 1
            print(f"FAIL {slug}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"ok   {slug}")
    print(f"\n{len(slugs) - bad}/{len(slugs)} clean")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
