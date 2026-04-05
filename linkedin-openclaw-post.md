# LinkedIn Post — OpenClaw API Decision

**Draft — April 4, 2026**

---

Today Anthropic officially cut off Claude Pro and Max subscribers from using their subscriptions to power third-party tools like OpenClaw. If you've been running agents through your flat-rate subscription, that stops working at noon PT today.

I saw this coming back in February.

When I started building the Tucson Daily Brief — an AI-powered local news pipeline that generates daily briefings, podcast episodes, and government meeting previews for the Tucson metro area — I made a deliberate architectural decision: every single AI call goes through the Anthropic API with my own API key. Not through my Claude Max subscription. Not through OAuth tokens. Pay-per-token from day one.

At the time, I was watching people spin up dozens of concurrent OpenClaw agents on their $20/month Pro plans, burning what industry estimates now peg at $1,000–5,000/day in equivalent API costs. The math never worked in Anthropic's favor, and I didn't want my production pipeline depending on a loophole.

The entire Tucson Daily Brief pipeline — a Sonnet 4.6 agent that writes the daily briefing, Haiku for podcast script condensation, four separate agenda mining pipelines covering Pima County, Tucson, Marana, and Oro Valley, plus a live transcription reporter for government meetings — costs me roughly $3–4/month in API fees. That's not a typo. Three to four dollars.

Today's crackdown changes nothing for me. My OpenClaw config has always been set to `"mode": "api_key"`. The subscription powers my interactive Claude Code and claude.ai sessions — exactly the use case Anthropic intended.

The lesson: when you're building on someone else's infrastructure, design for sustainability, not arbitrage. If your production system depends on underpriced access, you don't have a cost advantage — you have a liability.

---

*~280 words. Edit freely — this is your voice, not mine.*
