#!/usr/bin/env python3
"""Rank many plugin ideas by measured gap, using demand.py beside this file.

Usage:
  python3 radar.py <candidates.md> [--top N] [--json out.json]

candidates.md: one idea per line as `- primary term | synonym | synonym`.
Lines not starting with "- " are ignored. GitHub search allows ~30 requests a
minute when authenticated, so the scan pauses between ideas.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demand  # noqa: E402


def parse(path):
    ideas = []
    for line in Path(path).read_text().splitlines():
        if line.startswith("- "):
            terms = [t.strip() for t in line[2:].split("|") if t.strip()]
            if terms:
                ideas.append(terms)
    return ideas


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 15
    results = []
    for i, terms in enumerate(parse(sys.argv[1])):
        if i:
            time.sleep(2.5)
        r = demand.measure(terms)
        results.append(r)
        s = r["score"]
        print(f"  scanned {terms[0]:<28} gap {s['gap']:>6}", file=sys.stderr)
    results.sort(key=lambda r: -r["score"]["gap"])
    print(f"| Rank | Idea | Gap | Demand | Supply | Issues (reactions) | Official plugins | Smithery |")
    print("|---|---|---|---|---|---|---|---|")
    for n, r in enumerate(results[:top], 1):
        s, gi = r["score"], r["github_issues"]
        print(f"| {n} | {r['terms'][0]} | {s['gap']} | {s['demand']} | {s['supply']} | "
              f"{gi['count']} ({gi['reactions']}) | {len(r['official_plugins'])} | {r['smithery']['count']} |")
    print(f"\nFormula: {demand.SCORING}")
    print("Developer-facing demand only: industry ideas score low on GitHub/HN by nature; "
          "judge them on the brief's user research instead.")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
