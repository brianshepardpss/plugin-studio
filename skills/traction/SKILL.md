---
name: traction
description: Use when checking how published Claude plugins are doing, or when the user says "how are my plugins doing", "traction report", "update the dashboard", "collect stats", "who is using my plugin", or "is anyone installing it". Fetches GitHub traffic, stars, issues and .plugin downloads for every plugin in studio.json, keeps history, and scores each against its thresholds.
---

# Collect and report traction

1. Find studio.json (see the portfolio skill). For a demo with no published
   plugins, use `samples/studio.json` in this plugin's root with
   `--no-fetch --today 2026-09-01` (a fake portfolio frozen at day 31).
2. Run:
   ```
   python3 <this skill dir>/collect.py <studio.json> --html traction.html
   ```
   It appends to `studio-data/` beside studio.json. GitHub keeps only 14 days
   of traffic, so this must run at least every 13 days; daily is better. Offer
   to schedule it (a cron entry, or a scheduled Claude routine) the first
   time.
3. Report the table, then the few things that matter:
   - Which plugins moved since the last run and from which referrers.
   - Any outside issue or `request` issue: quote its title and link it.
     These are the strongest signal there is; someone took the time to ask.
   - Plugins approaching day 30: hand them to the decide skill.
4. Be honest about the metric: "cloners" is a sum of daily uniques (GitHub
   exposes no lifetime uniques), installs through the marketplace show up as
   clones, and Cowork users who download the .plugin file show up as
   downloads. Never present these as exact user counts.
