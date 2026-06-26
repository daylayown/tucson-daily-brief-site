---
name: tucson-daily-brief
description: >
  Fetch and summarize hyper-local news for Tucson and Pima County
  from validated RSS feeds and NWS weather APIs. Use when the user asks
  for a Tucson news briefing, local news update, daily digest, or morning
  brief. Also triggered by the scheduled morning cron job at 6:00 AM MST.
---

# Tucson Daily Brief

## Purpose

Produce a daily hyper-local news briefing for the Tucson/Pima County area.
This is a journalism product — prioritize accuracy, attribution, and local
relevance over volume.

## When to Use

- User asks for local news, Tucson briefing, daily digest, or "what's happening"
- Cron job triggers the briefing (6:00 AM MST)
- User asks about a specific local topic (city council, school board, weather, development)

## Sources — IMPORTANT

**`~/.openclaw/skills/tucson-daily-brief/references/sources.json` is the sole source of truth.**

Read that file at the start of every briefing run. Do NOT fetch any URL that is not
listed in sources.json. Do NOT hardcode or assume any feed URLs — if a source is not
in the JSON file, it does not exist.

**One exception:** editor-submitted tips in `~/.openclaw/workspace/EDITOR-TIPS.md` may carry a
vetted link you are allowed to fetch — see the **Editor Tips** section below.

The file organizes sources into tiers. Fetch them in this order:
1. `tier_1_primary` — always fetch first, these are the most important
2. `tier_2_broadcast` — fetch next
3. `tier_2_officials` — elected officials' social media accounts
4. `tier_3_supplemental` — fetch all of these
5. `tier_4_weather_safety` — always fetch, these are NWS APIs

For each source, use the `url` field to fetch. Handle failures gracefully —
if a source is down or returns an error, skip it and note the failure at the
end of the briefing. Do not write scripts to fetch sources. Use your built-in
fetch and browser tools directly.

### Source types

**RSS sources** (`"type": "rss"`) — Standard XML feeds. Parse items for headlines, summaries, and links.

**Bluesky sources** (`"type": "bluesky"`) — The URL returns JSON from the Bluesky public API (no auth needed). To extract posts:
- Post text is at `feed[].post.record.text`
- If a post links to an article, the URL is at `feed[].post.embed.external.uri` and the article title/description are in `embed.external.title` and `embed.external.description`
- Post timestamp is at `feed[].post.record.createdAt`
- Only consider posts from the last 24 hours
- For news outlet accounts (like AZPM): when a post embeds a link to a story that looks newsworthy, follow through to the article URL for full context, just as you would follow an RSS item's link
- For elected official accounts: scan for official statements, policy positions, or Arizona-specific news that is relevant to a Tucson story. These are not primary news sources — use them for context, quotes, and signal, not as story leads on their own
- Skip reposts/shares unless the content is highly relevant
- Attribute Bluesky sources the same way as any other: `📰 [AZPM](https://article-url)` (linking to the article, not to the Bluesky post)

**API/JSON sources** (`"type": "api_json"`) — NWS weather endpoints. See the Weather Section below.

Sources with `"status": "broken"` or `"status": "disabled"` should be skipped entirely — do not attempt to fetch them.


## Editor Tips (manual story injection)

Before ranking stories, read `~/.openclaw/workspace/EDITOR-TIPS.md`. It holds stories the
editor submitted by hand — leads that may not appear in any sources.json feed yet.

- Treat each tip whose **include-through** date is today or in the future as a candidate story,
  ranked by the normal Editorial Priorities. Skip tips whose include-through date has passed.
- **Exception to the sources.json-only rule:** you MAY fetch the source URL(s) listed in a tip.
  The editor has vetted them. Use them to confirm details and build a proper attribution link.
- Verify each tip against its link(s) and any newer coverage in the fetched feeds. Attribute to
  the outlet(s). If a story is single-source or not yet widely confirmed, soft-hedge ("is
  scheduled to," "according to [outlet]") and flag it as single-source per the Editorial
  Guidelines. Report neutrally — no framing or opinion, even on political events.
- Do not invent details beyond the tip and its linked source(s).


## Editorial Priorities

Rank stories in this order. Lead the briefing with the highest-priority story available.

1. **Government actions** — city council votes, county decisions, state legislation affecting Tucson, ballot measures
2. **Public safety** — major incidents, emergency alerts, law enforcement news. Not routine police blotter.
3. **Education** — TUSD, Amphitheater, Catalina Foothills school districts, University of Arizona
4. **Development & business** — new construction, business openings/closings, economic news, commercial real estate
5. **Community & events** — major events, cultural happenings, lifestyle. Only if genuinely significant.
6. **Weather** — always include, but position based on severity. Lead with weather if active alerts exist.

## Briefing Format

Use this exact structure:

```
Tucson Daily Brief — [Month Day, Year]

🚨 Public Safety
[Headline in bold.] [2-3 sentence summary in clear, neutral prose.]
📰 [Source Name](https://direct-article-url)

───

🏛️ Government
[Same format per story]

───

🏗️ Development & Business
[Same format per story]

───

🎉 Community & Events
[Same format per story]

───

⛈️ Weather — Tucson
[Active alerts status]

[Today's forecast: conditions, high/low, wind, precipitation chance]
[Tonight: conditions, low, precipitation chance]
[Tomorrow: conditions, high, precipitation chance]
[Outlook: 2-3 sentence summary of the week ahead]

📄 NWS Tucson Forecast API

───

Briefing saved: tucson-brief-YYYY-MM-DD.md
Sources fetched: [count that returned data] of [total count] ([list failed sources, or "all succeeded"])
Next update: 6:00 AM MST
```

### Format Rules

- Output ONLY the structured briefing — no conversational intros, greetings, sign-offs, or commentary (no "Good morning!", "Here's your brief", etc.)
- Do not add a summary or condensed version before or after the briefing
- The first line of output must be the title: "Tucson Daily Brief — [Month Day, Year]"
- Use section emojis as shown above (🚨 🏛️ 🏗️ 🎉 ⛈️)
- Use ─── as section dividers
- Each story gets a bold headline, 2-3 sentence summary, and 📰 source attribution with article link
- Source attribution MUST include a direct link to the original article using markdown syntax:
  `📰 [Source Name](https://url-to-the-specific-article)`
  For multi-source stories: `📰 [Tucson Agenda](https://url1), [AZPM](https://url2)`
  The URL should be the direct link to the article, not the source's homepage.
  If you cannot determine the direct article URL, use the source name without a link.
- Deduplicate: if the same story appears in multiple sources, merge them and cite all sources
- Target 7-12 stories total. Quality over quantity.
- Omit sections that have no stories rather than including filler
- Only report on sources that are actually in sources.json — do not invent or assume other sources

## Weather Section

The weather section must include the actual forecast, not just alert status.

1. Fetch the active alerts URL from sources.json (tier_4_weather_safety) — report any active alerts prominently
2. Fetch the point forecast URL from sources.json — get the `forecast` URL from the response
3. Fetch that forecast URL to get the detailed period-by-period forecast
4. Include: today's conditions/high/low/wind, tonight, tomorrow, and a 2-3 sentence outlook
5. If active alerts exist (warnings, watches, advisories), lead the weather section with them using ⚠️

## Editorial Guidelines

- Write in neutral, factual tone — this is journalism, not commentary
- Always attribute sources using their `name` field from sources.json with a direct article link: "📰 [Arizona Daily Star](https://tucson.com/...)" / "📰 [KGUN 9](https://url1), [Inside Tucson Business](https://url2)"
- If sources conflict on facts, note the discrepancy
- Do not editorialize or add opinion
- Flag anything that appears unverified or single-source
- Use AP style
- Exclude national/state news unless it directly impacts Tucson/Pima County
- Exclude sports unless it involves a major local institution (U of A) and is significant news, not routine game results
- Exclude sponsored content, affiliate content, and advertorials from sources

## Output

1. Save the briefing as markdown to `~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md`
   - Create the `briefings` directory if it doesn't exist
   - Do NOT send the briefing via Telegram — the downstream pipeline (`run_podcast.sh`) handles Telegram delivery automatically after the file is saved
2. If any sources failed to fetch, list them in the footer — but only sources that are in sources.json

## Known Issues (as of February 2026)

- Some Arizona Daily Star articles are paywalled. RSS summaries are usually sufficient; do not attempt to bypass paywalls.
