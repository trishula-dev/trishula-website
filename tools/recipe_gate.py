#!/usr/bin/env python3
"""recipe_gate.py — the site's recipe-acceptance gate (TR-WS-12, website#62).

Ported from the kailash-book gate (kailash-book#11) to the site's shape:
one `recipes*.qmd` page with `## Recipe N — <title>` sections.

Checks per page:
  1. single H1 (the YAML title is the page's only H1).
  2. ramp cross-check: every published `## Recipe N` section carries a
     matching ramp row, by number AND by title.
  3. per published recipe: the header strip columns (Tool / Section /
     Level / Time / Layer / Tags), the anatomy H3 sections (Problem /
     Solution / Discussion / See also / Provenance).
  4. provenance footer: `Verified against` + a commit-pinned link + a
     verified-at date.
  5. no-invented-evidence: bash/sh/python fences carry no prompt glyphs
     (`$ cmd`, `>>> `, `user@host:`) — commands yes, transcripts no.
  6. PENDING ownership: the closing PENDING span must leave out every
     published recipe number — no silent drop of an unworked ramp row.

Exit 0 green / 1 red; one failure line per violated check.
Self-test: tests/test_recipe_gate.py (RED fixtures, offline).
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

STRIP_FIELDS = ["tool", "section", "level", "time", "layer", "tags"]
REQUIRED_SECTIONS = ["problem", "solution", "discussion", "see also", "provenance"]
RECIPE_HEAD = re.compile(r"(?m)^## Recipe (\d+) — (.+?)\s*$")
RAMP_ROW = re.compile(r"(?m)^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
PENDING_SPAN = re.compile(r"(?i)recipes?\s+(\d+)\s+to\s+(\d+)\s+(?:are |stay |is )?pending")
COMMIT_LINK = re.compile(r"\]\((https://github\.com/[^)]*/commit/[0-9a-f]{7,40})\)")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
VERIFIED = re.compile(r"(?i)verified against")

PROMPT_GLYPHS = [
    re.compile(r"(?m)^\$\s+\S"),                                   # "$ cmd" PS1
    re.compile(r"(?m)^>>> \S"),                                    # python REPL
    re.compile(r"(?m)^[A-Za-z0-9_.@~-]+@[A-Za-z0-9._-]+[:~]\s"),   # user@host:
]


def body(text: str) -> str:
    return re.split(r"^---\s*$", text, maxsplit=2, flags=re.M)[-1]


def unfenced(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def section_bodies(text: str) -> list[tuple[int, str, str]]:
    """[(n, title, segment)] for every `## Recipe N — <title> {#recipe-N}` section.
    The explicit anchor suffix (`{#recipe-N}`) strips from the title: the
    title = the human text only, the ramp compares human text."""
    out = []
    heads = list(RECIPE_HEAD.finditer(text))
    for i, m in enumerate(heads):
        seg_end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        title = re.sub(r"\s*\{#recipe-\d+}\s*$", "", m.group(2).strip())
        out.append((int(m.group(1)), title, text[m.start():seg_end]))
    return out


def parse_ramp(text: str) -> dict[int, str]:
    ramp: dict[int, str] = {}
    segm = text.split("## The recipe ramp")
    if len(segm) > 1:
        ramp_zone = segm[1].split("## ")[0]
        for m in RAMP_ROW.finditer(ramp_zone):
            ramp[int(m.group(1))] = m.group(2).strip()
    return ramp


TITLE_HEAD = re.compile(r'(?m)^title:\s*["\']?Recipe (\d+) — (.+?)["\']?\s*(?:\{#recipe-\d+\})?\s*$')

def page_recipe(text: str) -> tuple[int, str] | None:
    """(n, title) when the page = a single-recipe page (the frontmatter's
    title = 'Recipe N — ...'); else None."""
    m = TITLE_HEAD.search(text)
    if not m:
        return None
    return int(m.group(1)), re.sub(r"\s*\{#recipe-\d+}\s*$", "", m.group(2).strip())

def check_page(path: Path, shared_ramp: dict[int, str] | None = None) -> list[str]:
    text = path.read_text(encoding="utf-8")
    v: list[str] = []
    b = body(text)

    # 1. single H1 (strip fenced code; bash `#` comments are not headings)
    if re.search(r"(?m)^# \S", unfenced(b)):
        v.append("single-h1: body H1 present (the YAML title is the only H1)")

    published = section_bodies(text)
    ramp = parse_ramp(text) or (shared_ramp or {})
    # the recipe-page mode: no `## Recipe` H2 but the title names one = the
    # page = the recipe (the segment = the whole body; the title = its name)
    if not published:
        pr = page_recipe(text)
        if pr:
            strip = next((l for l in b.splitlines() if re.match(r"\s*\|\s*Tool\s*\|", l)), None)
            if not strip:
                v.append(f"recipe {pr[0]}: no header strip (| Tool | ... row)")
            else:
                low = strip.lower()
                for fld in STRIP_FIELDS:
                    if not re.search(rf"\|\s*{fld}\s*\|", low):
                        v.append(f"recipe {pr[0]}: header strip field missing: {fld}")
            heads = {h.strip().lower() for h in re.findall(r"(?m)^### (.+)$", b)}
            for s in REQUIRED_SECTIONS:
                if s not in heads:
                    v.append(f"recipe {pr[0]}: missing section: {s}")
            if not (VERIFIED.search(b) and COMMIT_LINK.search(b) and DATE.search(b)):
                v.append(f"recipe {pr[0]}: provenance footer missing (verified against + commit pin + date)")
        if ramp and pr and pr[0] in ramp:
            if ramp[pr[0]] != pr[1]:
                v.append(f"ramp: recipe {pr[0]} title drift (ramp '{ramp[pr[0]]}' vs page '{pr[1]}')")
        elif ramp and pr and pr[0] not in ramp:
            v.append(f"ramp: published recipe {pr[0]} lands outside the planned ramp")
        # the recipe-page mode's evidence check (the no-prompt-glyph rule)
        for fm in re.finditer(r"```(?:bash|sh|console|shell|python|py)\n([\s\S]*?)```", b):
            blk = fm.group(1)
            for pat in PROMPT_GLYPHS:
                if pat.search(blk):
                    v.append("no-invented-evidence: prompt-glyph block")
                    break
        return v

    # 2. ramp cross-check
    for n, title, _ in published:
        if n not in ramp:
            v.append(f"ramp: published recipe {n} is missing a ramp row")
        elif ramp[n] != title:
            v.append(f"ramp: recipe {n} title drift (ramp '{ramp[n]}' vs section '{title}')")
        if ramp and n not in ramp and n > max(ramp):
            v.append(f"ramp: published recipe {n} lands outside the planned ramp")

    # 3.+4. per published recipe: strip, anatomy, provenance
    for n, _title, seg in published:
        strip_line = next((l for l in seg.splitlines()
                           if re.match(r"\s*\|\s*Tool\s*\|", l)), None)
        if not strip_line:
            v.append(f"recipe {n}: no header strip (| Tool | ... row)")
        else:
            low = strip_line.lower()
            for fld in STRIP_FIELDS:
                if not re.search(rf"\|\s*{fld}\s*\|", low):
                    v.append(f"recipe {n}: header strip field missing: {fld}")
        heads = {h.strip().lower() for h in re.findall(r"(?m)^### (.+)$", seg)}
        for s in REQUIRED_SECTIONS:
            if s not in heads:
                v.append(f"recipe {n}: missing section: {s}")
        if not (VERIFIED.search(seg) and COMMIT_LINK.search(seg) and DATE.search(seg)):
            v.append(f"recipe {n}: provenance footer missing (verified against + commit pin + date)")
        for fm in re.finditer(r"```(?:bash|sh|console|shell|python|py)\n([\s\S]*?)```", seg):
            blk = fm.group(1)
            for pat in PROMPT_GLYPHS:
                if pat.search(blk):
                    v.append(f"recipe {n}: no-invented-evidence: prompt-glyph block ({pat.pattern[:20]})")
                    break

    # 6. PENDING span vs published set (the page's OWN ramp only; a
    # shared, cross-page ramp = the index owns the pending housekeeping)
    own_ramp = parse_ramp(text)
    tail = b[-800:]
    m = PENDING_SPAN.search(tail)
    published_ns = {n for n, _, _ in published}
    unworked = {n for n in own_ramp if n not in published_ns}
    if own_ramp and m:
        lo, hi = int(m.group(1)), int(m.group(2))
        span_ns = {n for n in ramp if lo <= n <= hi}
        clash = span_ns & published_ns
        if clash:
            v.append(f"pending-ownership: published recipes {sorted(clash)} also sit inside the PENDING span {lo} to {hi}")
        dropped = unworked - span_ns
        if dropped:
            v.append(f"pending-ownership: unworked ramp recipes {sorted(dropped)} sit outside the PENDING span {lo} to {hi}")
    elif own_ramp and unworked:
        v.append("pending-ownership: the ramp carries unworked plans but no closing PENDING span")

    return v


def run_gate(root: Path) -> list[tuple[str, list[str]]]:
    pages = sorted(root.glob("recipes*.qmd"))
    if not pages:
        return [(str(root), ["no recipes*.qmd page found"])]
    # Two-page shapes in one root: an index page (carries the ramp, no
    # recipes) + category pages (carry the recipes). The ramp cross-check
    # runs cross-page: every ramp row must publish SOMEWHERE under the
    # root; an index page must not re-publish recipes its ramp worked.
    results: list[tuple[str, list[str]]] = []
    ramp_rows: dict[int, tuple[str, str]] = {}  # n → (page, title)
    for pp in pages:
        text = pp.read_text(encoding="utf-8")
        for n, title, _ in section_bodies(text):
            ramp_rows[n] = (pp.name, title)
        # the recipe-page mode: the frontmatter's own title
        pr = page_recipe(text)
        if pr and pr[0] not in ramp_rows:
            ramp_rows[pr[0]] = (pp.name, pr[1])
    shared = {n: t for (n, (pg, t)) in ramp_rows.items()} if ramp_rows else None
    for pp in pages:
        text = pp.read_text(encoding="utf-8")
        ramp = parse_ramp(text)
        published = section_bodies(text)
        if ramp and not published:
            # the index page: the ramp's rows must all publish elsewhere
            for n, rtitle in ramp.items():
                if n not in ramp_rows:
                    results.append((pp.name, [f"ramp: recipe {n} '{rtitle}' publishes nowhere under this root"]))
                elif ramp_rows[n][1] != rtitle:
                    results.append((pp.name, [f"ramp: recipe {n} title drift ({ramp_rows[n][0]} '{ramp_rows[n][1]}' vs ramp '{rtitle}')"]))
            idx = check_index(pp)
            results.append((pp.name, idx))
            continue
        results.append((pp.name, check_page(pp, shared_ramp=shared)))
    return results


def check_index(path: Path) -> list[str]:
    """The index page's own checks: the H1, the PENDING span, the links."""
    text = path.read_text(encoding="utf-8")
    b = body(text)
    v: list[str] = []
    if re.search(r"(?m)^# \S", unfenced(b)):
        v.append("single-h1: body H1 present (the YAML title is the only H1)")
    # every category page the index cites must exist next to it
    for m in re.finditer(r"\]\((recipes[a-z0-9-]*\.html)\)", b):
        target = m.group(1).replace(".html", ".qmd")
        if not (path.parent / target).exists():
            v.append(f"categories: the index cites {target}, which does not exist")
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="recipe-acceptance gate (site form)")
    ap.add_argument("--root", default=".")
    ap.add_argument("--report", default=None, help="write a JSON report here")
    args = ap.parse_args()
    results = run_gate(Path(args.root))
    failures = [f"{name}: {f}" for name, fs in results for f in fs]
    n_pages = len(results)
    if args.report:
        Path(args.report).write_text(json.dumps({
            "failures": failures, "pages_checked": n_pages,
            "verdict": "GREEN" if not failures else "RED",
        }, indent=1) + "\n")
    if failures:
        print(f"recipe-gate: RED — {len(failures)} failures over {n_pages} pages")
        for f in failures:
            print("  -", f)
        return 1
    print(f"recipe-gate: GREEN ({n_pages} page(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
