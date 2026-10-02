# Plugin Studio

Run a portfolio of Claude plugins like a studio: find the gaps with live
data, track every published plugin daily, and make a kill / iterate /
double-down call at day 30 against thresholds you set before launch.

Pairs with [Plugin Creator](https://github.com/brianshepardpss/plugin-creator-plugin),
which builds the plugins; Studio decides which ones to build and which ones
to keep.

Works in: Claude Code (needs Python 3 and the `gh` CLI logged in with push
access to your plugin repos, because GitHub only shows traffic to
collaborators).

## Install

```
/plugin marketplace add brianshepardpss/plugin-creator
/plugin install plugin-studio@plugin-creator
```

## Try it in 60 seconds

Ask: "Show me the traction report for the sample portfolio." It runs on a
bundled fake portfolio frozen at day 31 and shows every verdict type.

## What it does

| Piece | Purpose |
|---|---|
| `/plugin-studio:studio` | The loop: collect traction, write day-30 memos, rank the next gaps |
| radar skill | Ranks a list of ideas by live demand (GitHub issue reactions on the Claude repos, Hacker News) minus supply (official plugins, Smithery, npm). 46 seeded ideas included |
| portfolio skill | Keeps `studio.json`: repos, launch dates, day-30 thresholds |
| traction skill | Daily GitHub views, clones, stars, outside issues, `.plugin` downloads and referrers, with history kept beyond GitHub's 14-day window; HTML dashboard |
| decide skill | Day-30 memo: numbers vs thresholds, what people asked for, the call, and v2 scope |

## How the verdict works

At day 30: every threshold met is DOUBLE DOWN, any metric at 50% or more is
ITERATE, otherwise STOP. Before day 30, a plugin is ON TRACK if every metric
is on pace. "Cloners" is a sum of daily unique cloners, because GitHub exposes
no lifetime uniques. The formula is printed with every report.

## Privacy

Traction data comes from the GitHub API for your own repos and stays in
`studio-data/` on your machine. The radar sends your idea terms to public
APIs (GitHub search, Hacker News, Smithery, npm). Nothing is published or
posted.

## Feedback

Say "I wish this could..." and the request skill drafts an issue for you to
file. Nothing is sent automatically.

Not affiliated with or endorsed by Anthropic or GitHub.
