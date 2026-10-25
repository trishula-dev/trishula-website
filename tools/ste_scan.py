#!/usr/bin/env python3
"""ste_scan.py — the checkable ASD-STE100 audit for markdown/qmd prose.

Covers the four recurring, grep-shaped checks a docs pass needs before a PR:
  1. sentence length: prose sentences over N words (default 20), with
     markdown links collapsed to their label first (a [label](url) pair
     counts as its label's words, never the URL's);
  2. first-person tokens (I, we, my, our, mine, us) outside code fences;
  3. second-person tokens (you, your) outside code fences — advisory
     (reader-page voices like recipe Problems legitimately use "you");
  4. naked section tokens: a §N cite whose own line carries no markdown
     link, and any '.pdf' string (the public-surface residue class).

Tables (lines starting '|') stay unsentenced; lists count as prose. Code
fences strip first so quoted output and commands never inflate counts.

Run: python3 ste_scan.py FILE [FILE...]   (exits 0 green / 1 red)
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

FENCE = re.compile(r"```.*?```", re.S)
LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
URL = re.compile(r"https?://\S+")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
FIRST = re.compile(r"\b(I|we|my|our|mine|us)\b\s*", re.I)
SECOND = re.compile(r"\b(you|your)\b", re.I)
PDF = re.compile(r"\.pdf\b", re.I)


def prose_lines(text: str) -> str:
    """Drop fenced blocks + table rows; keep everything else (lists count)."""
    unfenced = FENCE.sub("", text)
    return "\n".join(l for l in unfenced.splitlines()
                     if not l.lstrip().startswith("|"))


def collapse(text: str) -> str:
    text = LINK.sub(lambda m: m.group(1), text)
    text = URL.sub("<url>", text)
    return text


def check_file(path: Path, max_words: int) -> list[tuple[str, bool]]:
    """[(message, advisory?)] for one file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    body = prose_lines(text)
    flat = collapse(body)
    out: list[tuple[str, bool]] = []
    for para in re.split(r"\n\s*\n", flat):
        for s in SENT_SPLIT.split(para.replace("\n", " ").strip()):
            s = s.strip()
            if not s:
                continue
            words = [w for w in s.split() if re.search(r"\w", w)]
            if len(words) > max_words:
                out.append((f"sentence over {max_words} words ({len(words)}): {s[:90]}", False))
    for line_no, line in enumerate(flat.splitlines(), 1):
        if FIRST.search(line):
            out.append((f"L{line_no}: first-person token: {line[:70]}", True))
        if SECOND.search(line):
            out.append((f"L{line_no}: second-person token (advisory): {line[:70]}", True))
        if PDF.search(line):
            out.append((f"L{line_no}: a .pdf string on the surface: {line[:70]}", False))
        if "§" in line and "](" not in line and not line.lstrip().startswith((">", "#")):
            out.append((f"L{line_no}: naked § token without a link: {line[:70]}", False))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="ASD-STE100 prose audit")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--max-words", type=int, default=20)
    args = ap.parse_args()
    failures, advisory = 0, 0
    for f in args.files:
        for msg, soft in check_file(f, args.max_words):
            print(f"{f.name}: {msg}")
            if soft:
                advisory += 1
            else:
                failures += 1
    if failures:
        print(f"ste-scan: RED — {failures} hard findings ({advisory} advisory)")
        return 1
    print(f"ste-scan: GREEN ({advisory} advisory)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
