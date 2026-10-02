---
name: radar
description: Use when deciding which Claude plugin to build next, or when the user says "what plugins are missing", "find gaps", "rank plugin ideas", "where is the demand", or "scan for opportunities". Ranks a list of ideas by measured gap (live demand minus existing supply) and explains the ranking.
---

# Rank plugin ideas by measured gap

1. Use `candidates.md` in this skill's directory, or a list the user gives
   (write it in the same `- term | synonym` format to a file first). Add the
   portfolio's own feature requests as candidates: read open issues labelled
   `request` on each published repo in studio.json (`gh issue list --repo
   <owner>/<repo> --label request`).
2. Run:
   ```
   python3 <this skill dir>/radar.py <candidates file> --top 15 --json radar.json
   ```
   It takes about 5-8 seconds per idea. Tell the user it is running.
3. Present the table, then add judgement the numbers cannot:
   - An official plugin that exists but is broken or thin (check its repo and
     issues) is still a gap; say so explicitly.
   - Industry ideas score near zero on developer channels by design. Rank
     them separately, by the size of the profession and whether the work runs
     on files people already have.
   - Note where many community MCP servers exist but no plugin packages a
     workflow on top: that is usually the opening.
4. Recommend the top three with one sentence each on the hero workflow, and
   offer to start the best one with `/plugin-creator:new` (from the
   plugin-creator plugin) or the plugin-brief skill.
