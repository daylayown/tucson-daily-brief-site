# NICHOLAS DE LEON

15700 N Port Star Trl, Catalina, AZ 85739
347-361-7974 | nicholas@daylayown.org
[daylayown.org](https://daylayown.org)

---

## PROFESSIONAL SUMMARY

Builder and journalist with 20 years in digital media and a sustained record of shipping production AI tools inside a major national newsroom. As Senior Reporter at Consumer Reports, I have designed, built, and deployed automated editorial systems now used by CR editorial staff — including a daily competitive intelligence brief for the Home Team, a weekly content freshness monitor, and a custom browser extension that solved an editorial price-tracking problem after conventional scraping failed. Outside CR, I run an AI-assisted civic journalism platform covering the Tucson metro (live meeting transcription, multi-vendor agenda mining, daily news synthesis) and ship a portfolio of independent AI builds across mobile, web, and Discord. I bridge two worlds that rarely overlap: 20 years of newsroom credibility with reporters and editors, and the hands-on engineering to make AI tools journalists will actually adopt. Working proficiency in Spanish and Portuguese.

---

## CORE COMPETENCIES

**Production AI Tooling for Newsrooms.** Hands-on developer of editorial AI systems shipping inside a national publication. Working fluency with the Anthropic API (Claude Sonnet 4.6, Haiku 4.5, Opus 4.6), server-side web search tools, multi-provider orchestration (Claude / Gemini / xAI), Deepgram real-time transcription, ElevenLabs and Voxtral TTS, browser-extension architecture (Manifest V3), RSS / Bluesky AT Protocol scraping, and cron-based automation. Cost-aware: every tool I ship has measured per-run economics.

**Strategic AI Communication.** Lead briefer for VP-level editorial leadership at Consumer Reports on generative AI use cases — translating personal building experience into concrete, costed adoption strategies for a national publication.

**Editorial Leadership.** Ten years in editor-level roles directing daily operations and managing staff and freelance reporters across digital-native newsrooms (Vice/Motherboard, Circa, News Corp's The Daily). Experience maintaining substantive standards in high-velocity environments.

**Multi-Platform Building.** Ship working products across mobile (React Native + Expo, TypeScript strict mode), web (vanilla and Astro), browser extensions (Manifest V3), Discord bots (discord.js), and static-site pipelines (Python + GitHub Pages). Use Claude Code as primary AI-assisted development environment.

**Investigative & Data Journalism.** Public-records reporting and data-driven narratives across tech infrastructure, energy policy, and consumer protection. Build Python scraping and structured-data tools to support my own reporting and that of colleagues.

**Bilingual / Bicultural.** Working proficiency in Spanish and Portuguese, with technical oversight experience. Linguistic and subject-matter lead for the Spanish-language localization of Consumer Reports' Security Planner, ensuring complex privacy and security concepts were both technically accurate and culturally accessible for Hispanic audiences.

---

## NEWSROOM AI TOOLING — CONSUMER REPORTS (2024–PRESENT)

A growing suite of production AI tools built solo and shipped to real CR editorial users. All built with Claude Code as primary development assistant, all instrumented for cost and outcome.

**CR Competitive Intelligence Brief.** Daily intelligence briefing for the CR Home Team editors covering coverage from ~10 competitor publications (Wirecutter, Tom's Guide, The Strategist, CNET, Good Housekeeping, Reviewed, CNN Underscored, Insider Reviews, et al.). Multi-source ingestion across RSS, Google News, and Bluesky AT Protocol with graceful fallbacks. Claude Haiku 4.5 for ranking and summarization. Runs at 1:00 AM ET nightly and delivers via email before editors begin their day. Architecture inspired by my Tucson Daily Brief civic pipeline.

**Editorial Content Freshness Monitor.** Weekly cron'd pipeline that classifies my CR articles by update urgency, autonomously searches for nationally relevant news using Claude Sonnet 4.6 with the server-side web search tool (~9 searches per run, ~236K input tokens), and generates a prioritized editorial briefing emailed to me each Thursday. **Operating cost: ~$1/run, ~$4/month.** Includes a written rollout proposal for scaling to the full CR editorial team.

**Editorial Price Tracker (Custom Browser Extension).** Built after Python scraping against major retailers achieved only ~35% success due to modern bot detection. Pivoted to a custom Manifest V3 browser extension that runs inside a real Brave/Chromium instance, sees pages exactly as a human user would, and extracts pricing data via CSS selectors and JSON-LD parsing. **Live test result: 81% capture rate** across 16 consumer products × 3 retailers each. Includes a Python analysis pipeline that flags week-over-week price swings for editorial follow-up. Currently in pilot rollout.

**Weekly Editorial Digest.** Top-10 stories of the week from Consumer Reports' RSS feed, curated by Claude (A/B tested across Haiku 4.5, Sonnet 4.6, and Opus 4.6 with documented quality and cost trade-offs), formatted in Markdown for editor review and WordPress publication.

**Interactive Print Components.** "QR code-to-web" troubleshooting components built for the Consumer Reports print magazine, bridging static print stories to live, updatable web experiences.

---

## INDEPENDENT PROJECTS

**Tucson Daily Brief** — *[tucsondailybrief.com](https://tucsondailybrief.com)*. Production civic journalism platform covering the Tucson metro. Daily AI-synthesized news brief published since February 2026. Original civic reporting features: (1) AI-assisted agenda mining for four municipal governments using four different civic-tech vendor platforms (Pima County via Legistar API, City of Tucson via Hyland OnBase PDFs, Marana and Oro Valley via Destiny Hosted scraping); (2) live AI meeting reporter built on Deepgram real-time transcription and Claude Sonnet 4.6, with scheduled `at`-job recording for both YouTube and Swagit/HLS livestreams; (3) human-reviewed post-meeting news report pipeline. Total operating cost: under $10/month. Designed with explicit editorial guardrails: auto-publish for forward-looking previews, mandatory human review before any news report ships, transparent disclosure of AI involvement.

**Deep Dugout** — *[deepdugout.com](https://deepdugout.com)*. AI-managed baseball simulation platform. All 30 MLB teams managed by Claude-powered AI managers making real-time tactical decisions (pitching changes, lineup adjustments, bullpen management). Three-beat launch in March 2026: public website, live Discord event simulating all 15 MLB Opening Day games simultaneously across 20 channels with real-time AI-generated play-by-play, and an open-source release of the engine. Astro 5 + Tailwind v4 + discord.js + Claude API + ElevenLabs. Recognized on LinkedIn and Reddit.

**Deep Dugout: World Cup Edition** — Same simulation engine extended to 48 national teams and 104 matches for the 2026 FIFA World Cup, with AI coach personalities derived from national football identities. Shipping before June 11, 2026.

**DreamCatch** — Cross-platform mobile dream journal app. React Native + Expo SDK 54, TypeScript strict mode, SQLite local-first storage, Zustand state management, NativeWind v4 styling. Multi-provider AI: Claude Haiku/Sonnet for dream analysis, Nano Banana 2 (Gemini) for illustration generation, Grok Imagine Video for animated dream sequences. Tiered Free/Pro monetization architecture with RevenueCat.

**Crosswording the Situation** — *[crosswordingthesituation.com](https://crosswordingthesituation.com)*. Daily news-themed mini crossword. Pipeline: scrapes ~400 headlines from Google News RSS plus 28-day Bluesky lookback across six major news organizations, generates a 5×5 grid with rotational symmetry from a 12,720-word list, sends both to Claude Sonnet 4.6 for news-themed clue generation, runs a second-pass dedup check, and writes the puzzle JSON. GitHub Actions cron daily at 2 AM MST. Custom iOS keyboard handling adapted from the Guardian crossword's approach.

---

## PROFESSIONAL EXPERIENCE

**Consumer Reports** — *Senior Reporter* (October 2017 – Present)
- Newsroom AI tooling (see dedicated section above).
- Strategic AI demonstrations and briefings for VP-level editorial leadership.
- High-volume explainer journalism for a national audience: hardware, WiFi standards, AI policy, consumer technology.
- Two feature-length narratives annually for the Consumer Reports print magazine.
- Regular national broadcast source: CBS, Sirius XM, others.

**Vice Media (Motherboard)** — *Technology Editor* (July 2015 – July 2017)
- Built Motherboard's first consumer-tech section from scratch; managed a small team of staff and freelancers.
- Directed real-time coverage of major breaking events including the 2017 WannaCry ransomware crisis.
- Led emerging-beat coverage of digital privacy, net neutrality, and the early cryptocurrency market.

**Circa News** — *Technology Editor* (January 2013 – June 2015)
- Led technology coverage for the world's first mobile-native news organization.
- Developed a non-linear story format (atomic, updatable units) and a Follow-system push notification model that delivered only new information — no redundant reading.
- Directed all coverage of the Apple and Google ecosystems during the formative years of the mobile-first economy.

**News Corp / The Daily** — *Deputy Technology Editor* (April 2011 – December 2012)
- Managed end-to-end operations of the technology section: full-time staff of three reporters plus a global freelance roster.
- Directed the daily editorial calendar for the world's first iPad-native newspaper.
- Collaborated with designers and video producers on early experiments in non-linear, tablet-first digital journalism.

**TechCrunch** — *Reporter* (March 2007 – April 2011)
- High-velocity reporting on hardware, gaming, consumer technology, and emerging internet culture during the peak of the digital blogging era.
- Early specialized coverage of WikiLeaks, Bitcoin, and digital rights, drawing on a background in hacker culture (2600 magazine).

---

## EDUCATION

**New York University** (2008) — B.A., Journalism | B.A., Political Science
