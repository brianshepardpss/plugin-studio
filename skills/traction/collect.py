#!/usr/bin/env python3
"""Collect and score traction for a portfolio of published plugins.

Usage:
  python3 collect.py <studio.json> [--html out.html] [--no-fetch] [--today YYYY-MM-DD]

studio.json:
  {"owner": "<github owner>",
   "plugins": [{"name": "x", "repo": "x", "launched": "2026-10-05",
                "thresholds": {"cloners": 150, "stars": 40, "requests": 5}}]}

Each run fetches (with the `gh` CLI, which must be logged in with push access
to the repos, since GitHub only shows traffic to collaborators):
  - daily views and clones for the last 14 days (merged into history, so
    running at least every 13 days loses nothing)
  - stars, forks, open issues, issues labelled `request`, issues opened by anyone but the owner
    (the `requests` metric), release asset
    downloads (.plugin files), top referrers
Data lives beside studio.json in studio-data/: daily.json (per-day traffic)
and snapshots.jsonl (one line per repo per run).

Scoring (printed with every report so it can be audited):
  cloners  = sum of daily unique cloners since launch (a person cloning on two
             different days counts twice; GitHub exposes no lifetime uniques)
  progress = metric / threshold, per metric
  verdict at day >= 30: DOUBLE DOWN if every metric >= 100% of threshold,
             ITERATE if any metric >= 50%, otherwise STOP.
  days 0-2: TOO EARLY (GitHub traffic lags by hours).
  days 3-29: ON TRACK if every metric >= (days/30) of threshold, else BEHIND.
"""
import datetime as dt
import html
import json
import subprocess
import sys
from pathlib import Path

METRICS = ("cloners", "stars", "requests")


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return {"_error": (r.stderr or r.stdout).strip()[:200]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_error": "bad json"}


def gh_count(query):
    d = gh("search/issues?q=" + query.replace(" ", "+") + "&per_page=1")
    return d.get("total_count", 0) if "_error" not in d else None


def fetch(owner, p, daily, snaps, today):
    full = f"{owner}/{p['repo']}"
    repo = gh(f"repos/{full}")
    if "_error" in repo:
        return {"repo": full, "error": repo["_error"]}
    hist = daily.setdefault(full, {})
    for kind in ("views", "clones"):
        t = gh(f"repos/{full}/traffic/{kind}")
        for row in t.get(kind, []) if "_error" not in t else []:
            day = row["timestamp"][:10]
            hist.setdefault(day, {})[kind] = row["count"]
            hist[day][f"{kind}_uniques"] = row["uniques"]
    rel = gh(f"repos/{full}/releases")
    downloads = sum(a.get("download_count", 0) for r in rel for a in r.get("assets", [])) \
        if isinstance(rel, list) else 0
    refs = gh(f"repos/{full}/traffic/popular/referrers")
    snap = {
        "date": today, "repo": full,
        "stars": repo.get("stargazers_count", 0), "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "requests": gh_count(f"repo:{full} label:request"),
        "outside_issues": gh_count(f"repo:{full} is:issue -author:{owner}"),
        "downloads": downloads,
        "referrers": [{"ref": r["referrer"], "uniques": r["uniques"]} for r in refs]
        if isinstance(refs, list) else [],
    }
    snaps.append(snap)
    return snap


def score(p, hist, snap, today):
    launched = p.get("launched")
    days = (dt.date.fromisoformat(today) - dt.date.fromisoformat(launched)).days if launched else 0
    since = {d: v for d, v in hist.items() if not launched or d >= launched}
    vals = {
        "cloners": sum(v.get("clones_uniques", 0) for v in since.values()),
        "viewers": sum(v.get("views_uniques", 0) for v in since.values()),
        "stars": snap.get("stars", 0),
        "requests": snap.get("outside_issues") or 0,
        "downloads": snap.get("downloads", 0),
    }
    th = p.get("thresholds", {})
    prog = {m: (vals[m] / th[m]) if th.get(m) else None for m in METRICS}
    known = [x for x in prog.values() if x is not None]
    if not launched:
        verdict = "NOT LAUNCHED"
    elif days >= 30:
        verdict = ("DOUBLE DOWN" if known and all(x >= 1 for x in known)
                   else "ITERATE" if any(x >= 0.5 for x in known) else "STOP")
    elif days < 3:
        verdict = "TOO EARLY"
    else:
        pace = days / 30
        verdict = "ON TRACK" if known and all(x >= pace for x in known) else "BEHIND"
    return {"name": p["name"], "days": days, "values": vals, "progress": prog,
            "verdict": verdict, "spark": [since[d].get("clones_uniques", 0) for d in sorted(since)][-30:]}


def report(rows):
    out = ["| Plugin | Day | Cloners | Viewers | Stars | Outside issues | .plugin downloads | Verdict |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        v = r["values"]
        out.append(f"| {r['name']} | {r['days']} | {v['cloners']} | {v['viewers']} | {v['stars']} | "
                   f"{v['requests']} | {v['downloads']} | {r['verdict']} |")
    return "\n".join(out)


def sparkline(vals, w=120, h=24):
    if not vals:
        return ""
    m = max(vals) or 1
    step = w / max(len(vals) - 1, 1)
    pts = " ".join(f"{i * step:.1f},{h - v / m * (h - 2) - 1:.1f}" for i, v in enumerate(vals))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true">'
            f'<polyline fill="none" stroke="currentColor" stroke-width="1.5" points="{pts}"/></svg>')


def html_page(rows, today):
    tr = []
    for r in rows:
        v = r["values"]
        tr.append(f"<tr><td>{html.escape(r['name'])}</td><td>{r['days']}</td><td>{v['cloners']}</td>"
                  f"<td>{sparkline(r['spark'])}</td><td>{v['viewers']}</td><td>{v['stars']}</td>"
                  f"<td>{v['requests']}</td><td>{v['downloads']}</td>"
                  f"<td class='v'>{html.escape(r['verdict'])}</td></tr>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Plugin Traction</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--mute:#666;--line:#e5e5e5}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#141414;--fg:#eee;--mute:#999;--line:#2a2a2a}}}}
:root[data-theme=dark]{{--bg:#141414;--fg:#eee;--mute:#999;--line:#2a2a2a}}
body{{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif;margin:0;padding:24px 16px}}
.wrap{{max-width:960px;margin:0 auto;overflow-x:auto}} table{{border-collapse:collapse;width:100%}}
th,td{{text-align:left;padding:8px;border-bottom:1px solid var(--line);white-space:nowrap}}
th{{color:var(--mute);font-weight:500}} .v{{font-weight:600}} p{{color:var(--mute)}}
</style></head><body><div class="wrap"><h1>Plugin traction</h1><p>As of {today}. Cloners = sum of
daily unique cloners since launch. Verdict rule: day 30+, every threshold met = DOUBLE DOWN, any at 50% =
ITERATE, else STOP.</p><table><thead><tr><th>Plugin</th><th>Day</th><th>Cloners</th><th>Trend</th>
<th>Viewers</th><th>Stars</th><th>Outside issues</th><th>Downloads</th><th>Verdict</th></tr></thead>
<tbody>{''.join(tr)}</tbody></table></div></body></html>"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg_path = Path(sys.argv[1]).resolve()
    cfg = json.loads(cfg_path.read_text())
    data = cfg_path.parent / "studio-data"
    data.mkdir(exist_ok=True)
    daily_f, snaps_f = data / "daily.json", data / "snapshots.jsonl"
    daily = json.loads(daily_f.read_text()) if daily_f.exists() else {}
    today = (sys.argv[sys.argv.index("--today") + 1] if "--today" in sys.argv
             else dt.date.today().isoformat())
    snaps, latest = [], {}
    if snaps_f.exists():
        for line in snaps_f.read_text().splitlines():
            s = json.loads(line)
            latest[s["repo"]] = s
    rows = []
    for p in cfg["plugins"]:
        full = f"{cfg['owner']}/{p['repo']}"
        if not p.get("launched"):
            rows.append(score(p, {}, {}, today))
            continue
        snap = latest.get(full, {}) if "--no-fetch" in sys.argv else fetch(cfg["owner"], p, daily, snaps, today)
        if "error" in snap:
            print(f"warn: {full}: {snap['error']}", file=sys.stderr)
            snap = latest.get(full, {})
        rows.append(score(p, daily.get(full, {}), snap, today))
    daily_f.write_text(json.dumps(daily, indent=1, sort_keys=True))
    with snaps_f.open("a") as f:
        for s in snaps:
            f.write(json.dumps(s) + "\n")
    print(report(rows))
    if "--html" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--html") + 1])
        out.write_text(html_page(rows, today))
        print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
