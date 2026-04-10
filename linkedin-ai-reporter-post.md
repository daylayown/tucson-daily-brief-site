Last night, my AI reporter covered its first government meeting. No human was in the room. The entire Oro Valley Town Council session — three hours, from gavel to adjournment — was captured, transcribed, and turned into a publishable news article. I reviewed it this morning, made a few edits, and hit publish.

Let me back up.

I've been building Tucson Daily Brief since February — an AI-powered local news site covering Tucson, Pima County, and surrounding municipalities. It started as a daily news briefing synthesized from local sources, then I added an automated "Meeting Watch" pipeline that reads government agendas and publishes "what to watch" previews before meetings happen. Four municipalities, all running on cron jobs, zero human intervention.

But agenda previews are table stakes. The real question was: Can I cover what actually happens in the meeting?

Turns out, yes. And tonight was the proof.

Here's how it works. When a government meeting goes live — whether that's a YouTube stream or an HLS livestream from a platform like Swagit — my pipeline connects directly to the stream using ffmpeg, converts the audio to raw PCM, and pipes it into Deepgram's Nova-2 speech-to-text model via WebSocket. In real time. The transcript builds segment by segment, with speaker diarization so you can tell who's talking, timestamps down to the fraction of a second, and confidence scores on every word.

When the meeting ends, the system detects it automatically. I built what I'm calling a "protected window" — the pipeline records for a minimum of four hours without interruption, because council meetings have executive sessions, recesses, and breaks that can produce long stretches of silence. You don't want your recorder giving up because the council took a 15-minute break to use the bathroom. After the protected window expires, a dead air timeout kicks in: 15 minutes of no speech, and the system gracefully shuts down.

Once that happens, the full transcript — every word, every speaker, every timestamp — gets handed to Claude Sonnet 4.6, which turns it into an AP-style news article. Dateline, lede, nut graf, the whole thing. Claude drafts it; I review it. That's a non-negotiable part of the editorial model. AI drafts, humans approve. No exceptions.

Tonight's Oro Valley meeting covered a PAG public art presentation by local students, a road safety report showing ten years of increasing pedestrian and cyclist fatalities, a debate over additional funding for the Stone Canyon preserve, and a handful of routine votes. The kind of meeting that, in most small cities, gets zero press coverage. Not because it's unimportant — because there's nobody there to cover it.

That's the whole point. Local journalism is in freefall. Newsrooms are gutted. City council meetings happen and nobody writes about them. The information is technically public, but functionally invisible. What I'm building doesn't replace journalists — it extends their reach. An AI reporter that never misses a meeting, never gets tired, and drafts a clean article for a human editor to review.

The cost? About $1.50 per meeting. That's Deepgram transcription plus one Claude API call. The entire Tucson Daily Brief pipeline — daily briefings, agenda mining across four municipalities, podcast generation, and now live meeting coverage — runs for about $3-4 per month. Everything was built with Claude Code.

I genuinely believe this has never been done before: a fully automated pipeline that monitors a live government meeting stream, transcribes it in real time, detects when the meeting ends, generates a news article, and sends it to an editor for review. End to end. No human in the loop until the editorial check.

This is what AI-assisted journalism looks like. Not replacing reporters. Covering the meetings nobody else can get to.

You can read tonight's Oro Valley article — and everything else — at tucsondailybrief.com.
