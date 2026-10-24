#!/usr/bin/env python3
"""test_recipe_gate.py — watched-RED self-test for the site recipe gate (website#62).

Each fixture violates exactly one rule: the gate REDs on it naming the
violation; the compliant fixture (green/) never appears. Per-fixture
invocations (isolated --root per run) keep each RED attributable.
Run: python3 tests/test_recipe_gate.py (exits 0 green / 1 red).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE.parent / "tools" / "recipe_gate.py"
FIXTURES = HERE / "fixtures" / "recipe_gate"

EXPECTED_FAILURE_FRAGMENTS = {
    "missing-section": "missing section: discussion",
    "ps1-transcript": "prompt-glyph",
    "no-provenance": "provenance footer missing",
    "body-h1": "body h1",
    "ramp-drift": "title drift",
    "pending-ownership": "pending-ownership",
}


def gate(root: Path):
    r = subprocess.run([sys.executable, str(GATE), "--root", str(root)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    failures = []
    for name, frag in EXPECTED_FAILURE_FRAGMENTS.items():
        rc, out = gate(FIXTURES / name)
        if rc == 0:
            failures.append(f"{name}: gate ran GREEN, expected RED")
        elif frag not in out.lower():
            failures.append(f"{name}: RED without the rule fragment '{frag}'")
    rc, out = gate(FIXTURES / "green")
    if rc != 0 or "GREEN" not in out:
        failures.append(f"green: compliant fixture flagged (rc={rc}): {out}")
    if not failures:
        print("test_recipe_gate: OK (fixtures RED per rule + compliant fixture GREEN)")
        return 0
    print("test_recipe_gate: RED (self-test)")
    for x in failures:
        print("  -", x)
    return 1


if __name__ == "__main__":
    sys.exit(main())
