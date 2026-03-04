# Tucson Daily Brief — Live Demo Script

**Audience:** ~20 University of Arizona students + professor
**Time:** 15–20 minutes (part of a 75-minute talk)
**Setup:** Have these open in tabs/windows before you start:

- Browser: tucsondailybrief.com (today's post)
- Browser: YouTube channel (@tucsondailybrief)
- Terminal: this project directory
- Editor: `sources.json`, `TUCSON-BRIEF.md`, `run_podcast.sh` ready to open
- Audio: today's podcast episode queued to play

---

## 1. "What happened in Tucson today?" (2 min)

Open the website.

> This was published at 6 AM this morning. No human touched it. No one wrote it, edited it, or hit a publish button.

Read a headline or two out loud — pick one the students would recognize. U of A sports, a local restaurant, something on campus. Let them see their city in the output.

Play 20–30 seconds of the podcast episode.

> Same content. Same pipeline. Website, podcast, YouTube — all from the same source. Let me show you how this works.

**If the site is down:** Open today's briefing markdown file directly and show the raw text. "Here's what it generated this morning — let me show you how it gets to the web."

---

## 2. The sources — editorial curation (3 min)

Open `~/.openclaw/workspace/skills/tucson-daily-brief/references/sources.json`.

> It starts here. These are RSS feeds — the same technology that's powered blogs and news readers since the early 2000s. I picked these the same way an editor picks their beat sources.

Scroll through and show the tiers.

> Arizona Daily Star and AZPM are tier 1 — most reliable, most relevant. KGUN 9 is tier 2. Tucson Foodie, Inside Tucson Business are supplemental. NWS weather API is its own tier because you always need weather.

> The AI doesn't decide what to trust. I do. That's the journalism part. Curation is an editorial act.

**Talking point if asked:** "Why not just scrape everything?" Because journalism is about judgment, not volume. More sources doesn't mean better — it means more noise.

---

## 3. The editorial playbook (4 min)

Open `~/.openclaw/workspace/TUCSON-BRIEF.md`. This is your best material — linger here.

> This is the AI's assignment desk. Think of it as training a junior reporter. Every morning, the AI reads this file and follows these instructions.

Point to the **editorial priorities** section.

> Government actions first. Public safety second. Education third. I made these decisions — the AI just follows the ranking. If city council voted on something, that leads. Not a restaurant opening.

Point to the **format rules**.

> Every story gets a bold headline, 2-3 sentence summary, and a source attribution that links directly to the original article. We always link back. That's the neighborly thing to do — these local reporters did the actual work.

Point to the **editorial guidelines**.

> "Write in neutral, factual tone — this is journalism, not commentary." "If sources conflict on facts, note the discrepancy." "Exclude sponsored content."

> Everything the AI does is constrained by what I wrote here. The quality of the output is directly tied to the quality of these instructions. Garbage instructions, garbage briefing. The AI amplifies editorial judgment — it doesn't replace it.

**Talking point if asked about hallucination:** "The AI only summarizes articles from the feeds I gave it. It doesn't make up stories because it's working from real RSS data, not its own knowledge. The instructions explicitly say: only report on sources in sources.json."

---

## 4. Today's output (2 min)

Open today's briefing markdown: `~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md`

> Here's what the AI produced this morning. Title, sections, headlines, summaries, source links. All following the playbook.

Optionally show `generate_post.py` briefly.

> One Python script. No frameworks, no dependencies. It reads this markdown, converts it to HTML, and rebuilds the index page.

Run it live if you want — it takes under a second:

```
python generate_post.py ~/.openclaw/workspace/briefings/tucson-brief-2026-03-06.md
```

Open the generated HTML in a browser. Show how the source citations are now clickable links to the original articles.

**If something breaks:** "Let me show you one I generated earlier" — open an existing post in `posts/`.

---

## 5. The full pipeline (3 min)

Open `~/.openclaw/skills/tucson-daily-brief/scripts/run_podcast.sh`.

> Every morning at 6:10 AM, one cron job runs this script. Let me walk you through it.

Walk top to bottom:

> 1. Find today's briefing markdown
> 2. Send it to Telegram — morning subscribers get it on their phone
> 3. Generate podcast audio using ElevenLabs text-to-speech
> 4. Upload the podcast to an RSS feed — that's how it gets to Apple Podcasts, Spotify
> 5. Generate a YouTube video with the audio
> 6. Upload to YouTube
> 7. Generate the blog post HTML
> 8. Git push to GitHub Pages — that's the website

> It's a shell script. Not a microservices architecture. Not Kubernetes. Not a team of engineers. A shell script and a cron job.

Mention the resilience lesson:

> Last week, YouTube authentication expired and the upload failed for 4 days. But the podcast, the blog, and the Telegram delivery kept running the whole time — because each step is wrapped so one failure doesn't kill the rest. That's a design decision I made after it bit me.

---

## 6. The big picture (1–2 min)

> Total Python: a few hundred lines. External dependencies: basically zero for the site. Hosting: free on GitHub Pages. The whole thing runs on my laptop's cron job.

> But here's what I want you to take away: the hard part was never the code. It was deciding what Tucson news matters, what sources to trust, what editorial standards to set, and how to present it. That's journalism. The AI handles the volume. The human handles the judgment.

> If you're interested in journalism, this isn't a threat to what you'd do — it's a tool. Someone still has to be the editor. Someone still has to decide what matters. That someone just has a much more powerful newsroom now.

---

## Backup plans

| Problem | Fallback |
|---|---|
| Website is down | Open a local HTML file from `posts/` in browser |
| Can't run generate_post.py | Show an already-generated post and explain what the script does |
| Podcast won't play | Skip it — mention it exists, show the YouTube channel instead |
| AI agent is slow/fails live | "Let me show you one from this morning" — open today's pre-generated briefing |
| Students ask about cost | ElevenLabs TTS is the main cost (~$5/month). Everything else is free or near-free. |
| Students ask about accuracy | The AI summarizes real articles from trusted feeds — it doesn't generate from its own knowledge. The editorial playbook constrains it. Errors are possible but rare with good source curation. |
| Students ask "can I build this?" | Yes. The entire site is a Python script, a CSS file, and a markdown format. The AI agent is the only complex part, and that's getting easier every month. |

---

## Before you go on stage

- [ ] Confirm the site is live and today's post is up
- [ ] Have today's podcast episode ready to play (queued, volume checked)
- [ ] Open all files in your editor so you're not navigating live
- [ ] Have a browser tab on the site, a tab on YouTube
- [ ] Test your screen sharing / projector setup
- [ ] If demoing generate_post.py live, do a dry run first
