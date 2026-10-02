#!/usr/bin/env python3
"""Measure demand and supply for a plugin idea. Standard library only.

Usage:
  python3 demand.py "gitlab" ["merge request" ...] [--json]

Each argument is a search term; the first is the primary name. Prints a
markdown report (or JSON) with:
  demand: GitHub issues on Claude repos (count + top by reactions),
          Hacker News stories (count + points)
  supply: official Anthropic marketplace matches, Smithery MCP servers,
          npm packages mentioning MCP
  gap:    a transparent score = demand_points - supply_points (see SCORING)

Set GITHUB_TOKEN (or have `gh` logged in) for higher GitHub rate limits.
Every number comes from a live API call; nothing is estimated.
"""
import json
import math
import os
import subprocess
import sys
import urllib.parse
import urllib.request

ISSUE_REPOS = ["anthropics/claude-code", "anthropics/claude-plugins-official",
               "anthropics/skills", "modelcontextprotocol/servers"]
MARKETPLACES = [
    "anthropics/claude-plugins-official/main/.claude-plugin/marketplace.json",
    "anthropics/knowledge-work-plugins/main/.claude-plugin/marketplace.json",
]
SCORING = ("demand = ln(1+issue_reactions) + ln(1+issue_count) + ln(1+hn_points)/2; "
           "supply = 3*official_matches + ln(1+smithery_servers) + ln(1+npm_packages)/2; "
           "gap = demand - supply")
UA = {"User-Agent": "plugin-creator-demand/1.0"}


def _token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True,
                              text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}


def github_issues(term, token):
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    repos = " ".join(f"repo:{r}" for r in ISSUE_REPOS)
    q = f'"{term}" in:title is:issue {repos}'
    url = ("https://api.github.com/search/issues?" +
           urllib.parse.urlencode({"q": q, "sort": "reactions", "order": "desc", "per_page": 10}))
    d = get(url, h)
    if "_error" in d:
        return {"error": d["_error"], "count": 0, "reactions": 0, "top": []}
    items = d.get("items", [])
    return {
        "count": d.get("total_count", 0),
        "reactions": sum(i["reactions"]["total_count"] for i in items),
        "top": [{"title": i["title"], "url": i["html_url"], "state": i["state"],
                 "reactions": i["reactions"]["total_count"]} for i in items[:5]],
    }


def hn(term):
    hits, seen, count, err = [], set(), 0, None
    for q in (f"{term} mcp", f"{term} claude"):
        url = ("https://hn.algolia.com/api/v1/search?" +
               urllib.parse.urlencode({"query": q, "tags": "story", "hitsPerPage": 20}))
        d = get(url)
        if "_error" in d:
            err = d["_error"]
            continue
        count += d.get("nbHits", 0)
        for x in d.get("hits", []):
            if x["objectID"] not in seen and term.lower() in (x.get("title") or "").lower():
                seen.add(x["objectID"])
                hits.append(x)
    if err and not hits:
        return {"error": err, "count": 0, "points": 0, "top": []}
    return {
        "count": len(hits),
        "points": sum(h.get("points") or 0 for h in hits),
        "top": [{"title": h["title"], "points": h.get("points"),
                 "url": f"https://news.ycombinator.com/item?id={h['objectID']}"}
                for h in sorted(hits, key=lambda h: -(h.get("points") or 0))[:5]],
    }


def official(terms):
    found = []
    for path in MARKETPLACES:
        d = get(f"https://raw.githubusercontent.com/{path}")
        for p in d.get("plugins", []) if isinstance(d, dict) else []:
            text = f"{p.get('name', '')} {p.get('description', '')}".lower()
            if any(t.lower() in text for t in terms):
                found.append({"name": p.get("name"), "marketplace": path.split("/")[1],
                              "description": (p.get("description") or "")[:120]})
    return found


def smithery(term):
    d = get("https://registry.smithery.ai/servers?" +
            urllib.parse.urlencode({"q": term, "pageSize": 100}))
    if "_error" in d:
        return {"error": d["_error"], "count": 0, "top": []}
    t = term.lower()
    servers = [s for s in d.get("servers", [])
               if t in " ".join(str(s.get(k) or "") for k in
                                ("qualifiedName", "displayName", "description")).lower()]
    return {
        "count": len(servers),
        "top": [{"name": s.get("qualifiedName"), "uses": s.get("useCount")} for s in servers[:5]],
    }


def npm(term):
    d = get("https://registry.npmjs.org/-/v1/search?" +
            urllib.parse.urlencode({"text": f"{term} keywords:mcp", "size": 250}))
    if "_error" in d:
        return {"error": d["_error"], "count": 0, "top": []}
    t = term.lower()
    hits = [o["package"] for o in d.get("objects", [])
            if t in o["package"]["name"].lower().replace("-", " ")
            or t in (o["package"].get("description") or "").lower()]
    return {"count": len(hits), "top": [p["name"] for p in hits[:5]]}


def measure(terms):
    token = _token()
    primary = terms[0]
    gi, h = github_issues(primary, token), hn(primary)
    off, sm, nm = official(terms), smithery(primary), npm(primary)
    demand = (math.log1p(gi["reactions"]) + math.log1p(gi["count"]) + math.log1p(h["points"]) / 2)
    supply = 3 * len(off) + math.log1p(sm["count"]) + math.log1p(nm["count"]) / 2
    return {"terms": terms, "github_issues": gi, "hacker_news": h, "official_plugins": off,
            "smithery": sm, "npm": nm,
            "score": {"demand": round(demand, 2), "supply": round(supply, 2),
                      "gap": round(demand - supply, 2), "formula": SCORING}}


def report(r):
    s, gi, h = r["score"], r["github_issues"], r["hacker_news"]
    out = [f"# Demand check: {', '.join(r['terms'])}", "",
           f"Gap score {s['gap']} (demand {s['demand']} - supply {s['supply']})",
           f"Formula: {s['formula']}", "", "## Demand",
           f"- GitHub issues on Claude repos: {gi['count']} matching titles, "
           f"{gi['reactions']} reactions on the top 10" + (f" (error: {gi['error']})" if gi.get("error") else "")]
    out += [f"  - {i['reactions']:>4} [{i['state']}] {i['title']} {i['url']}" for i in gi["top"]]
    out.append(f"- Hacker News stories with the term in the title: {h['count']}, {h['points']} points total"
               + (f" (error: {h['error']})" if h.get("error") else ""))
    out += [f"  - {i['points']:>4} {i['title']} {i['url']}" for i in h["top"]]
    out += ["", "## Supply", f"- Official Anthropic plugins matching: {len(r['official_plugins'])}"]
    out += [f"  - {p['name']} ({p['marketplace']}): {p['description']}" for p in r["official_plugins"][:8]]
    sm, nm = r["smithery"], r["npm"]
    out.append(f"- Smithery MCP servers naming the term (of top 100 hits): {sm['count']}" + (f" (error: {sm['error']})" if sm.get("error") else ""))
    out += [f"  - {x['name']} uses={x['uses']}" for x in sm["top"]]
    out.append(f"- npm MCP packages naming the term (of top 250 search hits): {nm['count']}" + (f" (error: {nm['error']})" if nm.get("error") else ""))
    out += [f"  - {x}" for x in nm["top"]]
    return "\n".join(out)


if __name__ == "__main__":
    terms = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not terms:
        sys.exit(__doc__)
    r = measure(terms)
    print(json.dumps(r, indent=2) if "--json" in sys.argv else report(r))
