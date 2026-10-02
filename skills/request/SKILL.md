---
name: request
description: Use when the user wishes Plugin Studio did something it does not, hits a gap or bug in it, or says things like "I wish this could", "can it also", "feature request", "this is missing", "report a bug", or "send feedback". Drafts a feature request the user can file themselves. Sends nothing automatically.
---

# Request a feature or report a problem with Plugin Studio

This skill never sends data anywhere. It writes a draft and gives the user a
link; filing is their choice.

1. Work out from the conversation what the user wanted, what they tried, and
   what happened. Ask at most one clarifying question if the ask is unclear.
2. Write the draft in this shape:

   ```
   Title: <one line, starts with a verb>

   What I was trying to do:
   <1-3 sentences, in the user's terms>

   What happened / what is missing:
   <1-3 sentences>

   Why it matters:
   <how often, how much time or money it would save>

   Plugin: Plugin Studio <version from the plugin manifest if known>
   ```

3. Remove anything private before showing it: names, emails, phone numbers,
   addresses, customer or patient or candidate details, API keys, internal
   URLs, file contents. Use placeholders like `<customer>`.
4. Show the user the full draft and say plainly: "Nothing has been sent. If
   you'd like to file this publicly, open the link below. You can edit it
   before submitting."
5. Build the link (URL-encode title and body):
   `https://github.com/brianshepardpss/plugin-studio/issues/new?labels=request&title=<title>&body=<body>`
   If the encoded URL is longer than 7000 characters, shorten the body and
   tell the user to paste the rest.
6. Offer a no-GitHub alternative: the user can email the same text to
   brian@press-start-studios.com.
