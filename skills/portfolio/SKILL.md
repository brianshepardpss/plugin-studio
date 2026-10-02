---
name: portfolio
description: Use when setting up or updating the list of plugins a studio tracks, or when the user says "add my plugin to tracking", "I launched a plugin", "set thresholds", "set up plugin studio", or "what am I tracking". Maintains studio.json, the single source of truth for launches and day-30 thresholds.
---

# Maintain studio.json

studio.json lives wherever the user keeps their studio (default: the current
project root). Shape:

```json
{
  "owner": "<github user or org that owns the plugin repos>",
  "plugins": [
    {"name": "listing-desk", "repo": "listing-desk", "launched": "2026-10-05",
     "thresholds": {"cloners": 150, "stars": 40, "requests": 10}}
  ]
}
```

1. If it does not exist, ask for the GitHub owner and create it. Check
   `gh auth status`; traffic data needs push access to the repos.
2. Adding a plugin: name, repo, launch date (the day it was public and
   announced, not the day it was built) and the day-30 thresholds. Take the
   thresholds from the plugin's BRIEF.md section 8 or LAUNCH.md. If none
   exist, propose defaults (cloners 150, stars 40, requests 10 for developer
   tools; cloners 75, stars 15, requests 5 for industry plugins) and ask the
   user to confirm. Thresholds are set BEFORE launch and are not edited
   after, except to fix a typo; say this when asked to lower one.
3. A plugin with no `launched` date is shown as NOT LAUNCHED and not scored.
4. After editing, run the traction skill once so the new repo starts
   accumulating history (GitHub keeps only 14 days of traffic).
