---
name: decide
description: Use when a published plugin reaches day 30, or when the user asks "should I keep working on this plugin", "kill or keep", "what should v2 be", or "which plugin should I double down on". Writes a decision memo from the traction data, the pre-set thresholds and the actual feedback.
---

# Day-30 decision memo

1. Run the traction skill first so the numbers are current.
2. For each plugin at day 30 or later, take the verdict collect.py computed
   (DOUBLE DOWN, ITERATE, STOP); do not re-litigate the thresholds.
3. Read every outside issue and `request` issue on the repo
   (`gh issue list --repo <owner>/<repo> --state all`), and the referrers.
   Group the asks into themes with counts.
4. Write `decisions/<plugin>-day30.md`:

   ```
   # <plugin> day-30 decision: <VERDICT>
   Numbers vs thresholds: <table>
   What people asked for: <themes, counts, links>
   Where they came from: <referrers>
   Decision: <one paragraph>
   If DOUBLE DOWN: v2 scope (3 items max, from the request themes), and
     whether it earns a landing page, a paid tier or a directory push.
   If ITERATE: the one change most likely to move the weakest metric, and a
     new 30-day window with the same thresholds.
   If STOP: archive note for the README, and what we learned for the radar.
   ```
5. Summarise all memos in one table for the user and recommend where the
   next week of effort goes.
