# Build Prompt: University Job Watcher

*Paste this entire file into a fresh Claude Code session in an empty directory (suggested: `~/claude-code-projects/uni-job-watch/`).*

---

# Project: University Job Watcher

## What you're building

A weekly automated Python script that scans the careers pages of selected universities (and a few academic job boards) for new faculty, fellowship, and staff openings that match my professional profile, scores each match for relevance using Claude, and emails me a digest of new high-relevance results. Same architectural family as my existing internal tools at Consumer Reports — single Python file, stdlib-heavy, cron-driven, email-delivered.

The goal is to stop manually checking university careers pages once a week. I have a strong-but-unusual professional profile, and most academic job listings are not relevant to me. The script should do the filtering so I only see things worth my time.

## Reference project (read but do NOT modify)

A working version of this same architecture exists at:

```
~/claude-code-projects/cr-content-audit/
```

**Read `~/claude-code-projects/cr-content-audit/CLAUDE.md` and `~/claude-code-projects/cr-content-audit/content_monitor.py`** as your primary architectural reference. That project does almost the same thing for a different input: cron'd weekly, Sonnet 4.6 + server-side web search tool, generates a prioritized briefing, emails it via Gmail SMTP. You should pattern-match heavily on its structure.

**Do not modify anything in `cr-content-audit/`.** It is a working production tool. This new project should be entirely self-contained in its own directory.

## Architecture (the most important section — read carefully)

**Use Anthropic's server-side web search tool. Do NOT scrape university career pages directly.**

University careers pages run on enterprise HR systems (Workday, Cornerstone, iCIMS, PageUp). They are JavaScript-rendered and aggressively bot-resistant. I learned this lesson the hard way on a previous project (`cr-price-tracker`) where Python scraping with `requests` + BeautifulSoup achieved only ~35% success and we had to pivot to a browser extension. Do not repeat that mistake. The right tool here is the same one `cr-content-audit` uses: pass the search task to Claude Sonnet 4.6 with the `web_search_20250305` server-side tool and let Claude run the searches autonomously.

The pipeline:

```
1. Load profile.md         → My profile / what I'd take / what I'd skip
2. Load targets.json       → List of universities and job boards to scan
3. Load seen.json          → Job IDs/URLs already emailed about (dedup)
4. Single Sonnet 4.6 call with web_search_20250305 tool:
   - Sonnet receives my profile + the target list + the dedup list
   - Sonnet autonomously runs ~5-15 web searches across the targets
   - Sonnet returns structured JSON: list of candidate jobs with title,
     org, URL, location, brief description, and relevance score 1-10
5. Filter:                 → Keep only score >= 6 AND not in seen.json
6. Format email:           → Markdown digest with top matches first
7. Send via Gmail SMTP     → Same setup as cr-content-audit
8. Update seen.json        → Append the new job IDs
9. Log to cron.log         → Plaintext, append-only
```

A `--dry-run` flag should print the email body to stdout instead of sending it, and should NOT update `seen.json`. This is critical for testing without polluting state.

## My profile (use this verbatim in the system prompt)

I am Nicholas De Leon, a 20-year tech journalist. I'm currently a Senior Reporter at Consumer Reports (since 2017), where in addition to my regular reporting on hardware, WiFi, and AI policy, I have built and shipped a growing suite of production AI tools used by CR editorial staff: a TTS audio pipeline (~80% production time reduction), a daily competitive intelligence brief, a weekly content freshness monitor, and a custom Manifest V3 browser extension for editorial price tracking. Outside CR I run Tucson Daily Brief (tucsondailybrief.com), an AI-assisted civic journalism platform with daily news synthesis, multi-vendor agenda mining for four municipal governments, a live AI meeting reporter built on Deepgram + Claude, and a human-reviewed news report pipeline. I also build other things — a baseball simulation platform (Deep Dugout), a daily news crossword, a mobile app, etc. Earlier in my career I held editor titles at Vice/Motherboard, Circa News, and News Corp's The Daily, and was a reporter at TechCrunch. NYU 2008 BA in Journalism and Political Science. Bilingual Spanish (professional proficiency). Based in Catalina, Arizona. Willing to relocate anywhere globally for the right opportunity.

**What I am genuinely interested in:**
- Professor of Practice positions in journalism, communication, or digital media (teaching-track, no PhD required)
- Practitioner-in-Residence / Executive-in-Residence appointments
- Visiting Fellow / Research Fellow positions in computational journalism, journalism + AI, or local news
- Staff director / staff lead roles for journalism schools' applied or research labs (Knight Lab type)
- Newsroom innovation / editorial AI roles inside university-affiliated newsrooms
- AI / computational journalism lecturer positions
- Endowed chairs that explicitly value industry experience (e.g., Knight Chairs)
- Director / Associate Director roles at journalism research centers (Tow Center, Reynolds Journalism Institute, Knight Lab, etc.)
- Postdoctoral fellowships for journalists (Stanford JSK, Reuters Institute, Nieman, Knight-Wallace, Tow-Knight)
- Anything explicitly bridging AI and journalism

**What I should NOT be flagged about:**
- Tenure-track positions that strictly require a PhD with no "or equivalent professional experience" language
- Assistant Professor positions in pure communication theory, media studies, or rhetoric without an AI/data/applied component
- Adjunct or part-time lecturer roles below my career level
- Pure computer science faculty positions without journalism overlap
- Internships, graduate assistantships, or any role aimed at students or recent graduates
- Administrative roles (finance, HR, facilities, advancement)
- Public relations / marketing communications positions
- Any role with "entry-level," "0-3 years experience," "associate" (in the junior sense), or "intern" in the title

## Initial target list (`targets.json`)

Start with these. The structure should make it trivial to add more later — I want to expand the list over time.

```json
[
  {
    "name": "University of Arizona",
    "careers_url": "https://talent.arizona.edu/",
    "search_hint": "site:talent.arizona.edu OR site:arizona.edu/jobs",
    "priority": "high"
  },
  {
    "name": "Arizona State University",
    "careers_url": "https://cfo.asu.edu/applicant",
    "search_hint": "site:asu.edu/jobs OR site:asu.edu/careers OR site:cfo.asu.edu",
    "priority": "high"
  },
  {
    "name": "AEJMC Job Portal",
    "careers_url": "https://www.aejmc.org/job-portal/listings",
    "search_hint": "site:aejmc.org/job-portal",
    "priority": "high"
  },
  {
    "name": "Communication and Media Studies Academic Jobs Wiki",
    "careers_url": "https://academicjobs.fandom.com/wiki/Communication_and_Media_Studies_2025-2026",
    "search_hint": "site:academicjobs.fandom.com Communication Media Studies",
    "priority": "medium"
  },
  {
    "name": "HigherEdJobs Journalism",
    "careers_url": "https://www.higheredjobs.com/faculty/search.cfm?JobCat=132",
    "search_hint": "site:higheredjobs.com journalism faculty",
    "priority": "medium"
  }
]
```

The University of Arizona and Arizona State University are my top priorities (I live in Arizona). Build the script so adding more schools later is a one-line config change.

## File structure to produce

```
uni-job-watch/
├── README.md              # Brief setup + run instructions
├── CLAUDE.md              # Notes on architecture, design decisions, gotchas
├── job_watch.py           # The main script (single file, <300 lines)
├── targets.json           # University/board list (above)
├── profile.md             # My profile (above) — easy to edit
├── seen.json              # Dedup state (start as [])
├── .env.example           # Template for .env credentials
├── .env                   # Real credentials (gitignored)
├── .gitignore             # Excludes .env, cron.log, __pycache__/, .venv/
├── requirements.txt       # anthropic, python-dotenv (minimal)
└── cron.log               # Cron output (gitignored)
```

## `job_watch.py` design

Single file, ~200-300 lines. Stdlib-heavy. Use the `anthropic` Python SDK for the API call. CLI flags via `argparse`:

- `--dry-run` — prints email body to stdout, does NOT send, does NOT update seen.json
- `--limit N` — cap the number of new jobs in the digest (default 20, useful for first run)
- `--reset-seen` — wipes seen.json (use with caution; useful when changing the profile)
- `--target NAME` — only scan one target (debugging aid)

Key functions:

- `load_profile()` — read `profile.md` as a string
- `load_targets()` — read `targets.json` as list of dicts
- `load_seen()` — read `seen.json` as a set of job identifiers (URL or `org+title` hash)
- `save_seen(new_set)` — write back atomically (write to tmp, rename)
- `search_jobs(profile, targets, seen)` — single Anthropic API call with `web_search_20250305` tool. Returns parsed list of candidate jobs.
- `score_and_filter(candidates, seen)` — Claude has already scored, this just drops dupes and below-threshold matches
- `format_email(matches)` — markdown digest
- `send_email(body)` — Gmail SMTP
- `main()` — orchestration with argparse

## Anthropic API call shape

Use the messages endpoint with tools. The model should be `claude-sonnet-4-6` (the current Sonnet — confirm the exact model ID against `cr-content-audit/content_monitor.py` for consistency).

Pseudocode:

```python
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8000,
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 15
    }],
    system=SYSTEM_PROMPT,  # contains the profile + exclusions
    messages=[{
        "role": "user",
        "content": (
            "Search the following university careers pages and academic job boards "
            "for newly posted faculty, fellowship, or staff positions that match my profile. "
            "For each potential match, return JSON with: title, organization, location, url, "
            "one_paragraph_summary, why_it_matches, relevance_score (1-10). "
            "Return ONLY valid JSON in a fenced ```json code block, nothing else.\n\n"
            f"TARGETS:\n{json.dumps(targets, indent=2)}\n\n"
            f"ALREADY SEEN (do not return these):\n{json.dumps(list(seen))}\n\n"
            "Aim for 5-15 web searches across the targets. Be thorough but not exhaustive — "
            "focus on what's been posted recently. If a target has no relevant new postings, skip it."
        )
    }]
)
```

Parse the assistant's final text response, extract the JSON block, and process. Handle malformed JSON gracefully (log + fall back to empty list).

## Email format

Markdown, sent as `text/plain` via Gmail SMTP. Subject: `Uni Job Watch — {N} new matches ({date})`. Body shape:

```
University Job Watch — Weekly Digest
{date}

Found {N} new jobs matching your profile. Top matches first.

═══════════════════════════════════════════════
1. {title}
   {organization} — {location}
   Relevance: {score}/10
   {url}

   {one_paragraph_summary}

   Why this matches: {why_it_matches}

═══════════════════════════════════════════════
2. {title}
   ...

═══════════════════════════════════════════════
{footer with run timestamp + total searches performed}
```

If zero new matches, still send a brief "no new matches this week" email — I want to know the script ran successfully even when there's nothing to report. Or: skip the email entirely on zero matches and just log it. Your call — pick one and document it in CLAUDE.md.

## Environment variables (`.env.example`)

```
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_ADDRESS=yesdeleon@gmail.com
GMAIL_APP_PASSWORD=...   # NOT my regular Gmail password
NOTIFY_EMAIL=nicholas@daylayown.org
```

The Gmail SMTP setup is the same as in `cr-content-audit/.env.example` — copy that pattern. Load `.env` by absolute path (`Path(__file__).parent / ".env"`) so cron can find it regardless of working directory.

## Cron entry

After confirming the script works with `--dry-run`, install a cron entry that runs Mondays at 11:00 AM MST (matches my `cr-content-audit` cadence — Mondays are when I want job-search context to start the week). Don't actually install the cron yourself; print the line and instruct me to add it manually:

```
0 11 * * 1 /home/nicholas/claude-code-projects/uni-job-watch/.venv/bin/python /home/nicholas/claude-code-projects/uni-job-watch/job_watch.py >> /home/nicholas/claude-code-projects/uni-job-watch/cron.log 2>&1
```

## Setup commands

The README should document the standard sequence:

```bash
cd ~/claude-code-projects/uni-job-watch
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # then edit with real credentials
.venv/bin/python job_watch.py --dry-run --limit 5  # smoke test
.venv/bin/python job_watch.py --dry-run            # full preview
.venv/bin/python job_watch.py                      # real run, sends email
```

## Dedup strategy

The dedup key should be **stable across re-postings of the same job**. URL is unreliable (job systems sometimes generate new URLs for the same role). Use a normalized identifier:

```python
def job_key(org: str, title: str, location: str) -> str:
    norm = lambda s: re.sub(r'\s+', ' ', s.lower().strip())
    return f"{norm(org)}|{norm(title)}|{norm(location)}"
```

Store these as a JSON list in `seen.json`. Load as a set for O(1) lookups.

## Things to handle gracefully

- **Web search returns nothing** → log and email "no new matches this week" (or skip; document the choice)
- **API returns malformed JSON** → log the raw response, fall back to no matches, don't crash
- **SMTP fails** → log the failure and ALSO print the email body to stdout, so I don't lose the digest
- **`seen.json` doesn't exist on first run** → treat as empty set
- **`targets.json` is missing or malformed** → exit with a clear error message
- **API key is missing** → exit with a clear error message

Never silently swallow errors. Always log to `cron.log` with timestamps. The `cr-content-audit` project handles all of these — copy the patterns.

## Things NOT to build

Resist scope creep. Out of scope for v1:

- A web UI
- A database (JSON files are fine)
- Slack / Telegram delivery (email only for now)
- Multi-user support (single-user, single-profile)
- Automatic application generation (the script surfaces jobs; I write the cover letters)
- Job description archiving (we keep URLs; the JD lives at the URL)
- Salary parsing or filtering (relevance score is enough)
- A linter / test suite (single file, eyeball it)
- Async / parallel API calls (one Sonnet call per run is fine)

If something seems clever to add but isn't on the explicit feature list above, **don't add it**. I'll iterate after I see v1 working.

## What "done" looks like

1. `python job_watch.py --dry-run --limit 5` prints a plausible email body with 0–5 fake-but-format-correct entries based on real searches
2. `python job_watch.py --dry-run` prints a fuller version with actual jobs from the live targets
3. `python job_watch.py` (no flags) sends a real email to my address and updates `seen.json`
4. Re-running immediately produces zero new matches (dedup works)
5. The cron line is printed for me to install manually
6. README has the setup and run commands
7. CLAUDE.md documents the architecture, the gotchas you encountered, and any non-obvious design decisions

## Final note

The most important thing in this whole project is **the prompt that goes to Sonnet** — the system prompt and the user message I sketched above. The relevance of the results lives or dies on whether that prompt accurately describes my profile and exclusions. Spend disproportionate time getting the prompt right and verifying its output on a `--dry-run` before considering the project done. If the first dry-run surfaces irrelevant noise (lots of adjunct positions, tenure-track ling/comp roles, internships), tighten the exclusion language in the system prompt and re-run. Iterate until the noise floor is acceptable.

Pattern-match on `cr-content-audit/content_monitor.py` for everything else — file layout, env loading, error handling, email shape, cron pattern. That's the proven template; this project is its sibling.

Build it.
