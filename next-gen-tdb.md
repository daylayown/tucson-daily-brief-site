# Next-Generation Tucson Daily Brief

## My conclusion

The next level is not more AI-written articles. It is a **Tucson civic-memory system**: every public promise, vote, vendor, contract, payment, request, response, denial, document passage, and video timestamp becomes structured evidence that can be followed across months and jurisdictions.

You have already solved collection unusually well. The repository contains four-government agenda mining, roughly 53 hours of meeting transcripts, 21 post-meeting reports, development and liquor monitors, 3,995 archived Tucson Water advisories, social/audio production, and a 2,955-chunk RAG index.

What is missing is the connective tissue:

```text
Public activity → immutable evidence → relationships and deadlines
              → ranked reporting packets → human reporting → measured impact
```

That is where AI becomes transformative rather than merely productive.

## What yesterday’s records pipeline revealed

The design is fundamentally sound:

- AI identifies possible leads.
- Statutory language and verified custodians are deterministic.
- Nothing sends automatically.
- A second model now checks facts and prior disclosure.
- Human review remains mandatory.

That follows the project’s strongest rule: “derive, don’t ask a model” and keep original reporting human-reviewed ([CLAUDE.md](CLAUDE.md#standing-rules)).

But the first batch exposed the next problem:

- It produced **63 automated drafts from 21 reports—exactly the maximum three from every report**, despite the prompt saying zero should be normal.
- With six hand-written replacements/additions, the directory now has **69 drafts**.
- Roughly half are marked high urgency.
- At least two model requests were routed to the wrong custodian and needed a hand-written replacement ([PCAO replacement draft](records-requests/drafts/2026-07-22-pcao-french-plea-designation-and-ois-intake.md)).
- The prompt requires verbatim source quotations, but the code does not programmatically validate them before writing the draft ([foia_lead_spotter.py](foia_lead_spotter.py)).
- The existing batch predates the new verification pass and contains no rendered verification blocks.

In other words, it currently creates a **request firehose**, not an editor’s queue. Automating submission would amplify that problem. The valuable next step is automating selection, tracking, document intake, and follow-through.

There is also a compounding-source issue:

```text
Transcript → AI-written report → AI lead detector → AI web verifier → request
```

The request generator sees the prose product, not the primary transcript, agenda passage, or packet page. Each model pass can subtly reinterpret the previous one. Future leads should carry an exact source pointer—file, page or timestamp, and quoted span—from the primary evidence.

## The new system I would build: TDB Evidence Desk

The core should be a private evidence ledger, not another public section. Each record would have:

- A canonical entity: person, agency, LLC, address, project, contract, case, program.
- An event: vote, promise, payment, amendment, filing, request, response.
- An immutable source: document hash, URL, capture date, page or video timecode.
- An exact source span.
- Status: machine-extracted, human-confirmed, contradicted, superseded.
- Connections to prior TDB reporting.
- A follow-up date and unanswered question.

LLMs would propose entries and connections. Deterministic validators and a human would confirm them. Prose would be generated from confirmed evidence—not used as the database.

This would also cure a current limitation of ChatTDB: its corpus walker indexes briefs, reports, previews, agendas, filings, and development cases, but not `in-depth/` investigations or primary returned records ([build_index.py](rag/build_index.py)). The upgraded ChatTDB could answer with page-level documents and meeting timecodes, not merely links to TDB articles.

## High-impact AI uses that are genuinely additive

| Idea | What AI makes possible | First Tucson application |
|---|---|---|
| **Records-return auditor** | Inventory hundreds of returned files; OCR them; detect duplicates, missing date ranges, Bates-number gaps, inconsistent redactions, and requested items that were not produced | Audit the Rio Nuevo, PCAO, and downtown-security responses against the exact requests |
| **Contract-drift detector** | Align an original agreement with amendments, change orders, invoices, and payments; extract obligations and show how cost, scope, or deadlines changed | Empire/Rio Nuevo, Vanderbilt Farms, Pima broadband, Marana developer reimbursements |
| **Silent-edit monitor** | Archive every agenda packet and attachment version; semantically redline late uploads, changed ordinances, replaced staff reports, and removed files | “What changed between Friday’s packet and Tuesday’s vote?” across all five bodies |
| **Regional influence graph** | Resolve LLCs, addresses, vendors, attorneys, consultants, property owners, campaign donors, and projects across otherwise incompatible datasets | Find the same development interests appearing before Tucson, Pima County, Marana, Oro Valley, and Rio Nuevo |
| **Policy-lineage detector** | Compare ordinance, consultant, vendor, and public-comment language; identify highly similar text and trace where wording first appeared | Flock policies, heat rules, data-center conditions, community-facilities districts |
| **Crisis timeline compiler** | Align dispatch logs, incident reports, video, body camera, 911 audio, staffing records, and public statements to a common clock | Reconstruct the July 19 downtown shooting response minute by minute |
| **Local-impact radar** | Monitor state and federal regulations, grants, enforcement actions, and funding notices; join them to local agencies and projects | CAP cuts, housing grants, border-security funding, school funding, environmental rules |
| **Adversarial reporting agent** | Read a draft as a skeptical editor: identify unsupported claims, missing affected voices, strongest counterarguments, and records that could falsify the thesis | Run before every In Depth story, especially Rio Nuevo and public safety |

The most distinctive public content formats would be:

- **The Receipts:** a story accompanied by highlighted source passages and playable meeting timestamps.
- **What They Promised:** a living register of dated commitments and whether they happened.
- **Redline Tucson:** material changes quietly made to public documents.
- **Public Record of Public Records:** response time, cost, completeness, exemptions, and outcomes by agency.
- **Case files:** what is known, disputed, requested, received, and still unanswered—updated rather than rewritten from scratch.

Your existing promise tracker, semantic alerts, and anomaly detection ideas are already the correct direction ([ROADMAP.md](ROADMAP.md#roadmap-ai-forward-tools-beyond-rag-net-new-ideas-2026-06-23)). The evidence ledger would make them reliable instead of separate model experiments.

## The strongest first investigations

I would concentrate the records program on four pilots rather than 69 requests:

1. **Rio Nuevo: approved versus actually paid.**  
   The planned ledger already identifies the essential distinction between approved amounts, disbursements, promised results, and compliance ([RIO-NUEVO-PIPELINE-PLAN.md](RIO-NUEVO-PIPELINE-PLAN.md#the-three-tiers)). Empire is the first row, not the whole story.

2. **The downtown public-safety money map.**  
   Join TPD deployment funding, Rio Nuevo reimbursements, Downtown Tucson Partnership contracts, transit security, VIVA, and after-action records. The output should show who paid whom, for what coverage, under what performance expectations.

3. **South Tucson’s Flock aftermath.**  
   Not merely whether cameras were removed: hardware disposition, retained data, vendor access after termination, final costs, and whether every downstream agency’s access was revoked.

4. **The government promise audit.**  
   Extract every “return in 90 days,” “staff will report back,” “study is underway,” and “implementation by” statement from the existing transcript corpus. Start with Tucson lane-closure fees, housing-fee relief, police-review data, heat enforcement, and development obligations.

The fourth is technically already on your roadmap, but it is the perfect bridge between meeting automation and records reporting: when a deadline passes without visible action, the request drafts itself from confirmed evidence.

## A practical 90-day sequence

### First two weeks

- Do not send the 69-request backlog wholesale.
- Score each lead on public impact, exclusivity, specificity, expected availability, urgency, and reporting capacity.
- Select three consequential requests and one likely quick fulfillment.
- Create a request registry with statuses such as proposed, approved, filed, acknowledged, clarified, fee quoted, partial production, complete, denied, appealed, and published.
- Add deterministic validation for exact source spans, custodian routing, dates, duplicate requests, and overly broad phrases.

### Days 15–45

- Build the evidence ledger and page/timecode citation format.
- Change the meeting reporter to emit structured facts, votes, promises, and source segments alongside prose. Its current contract asks directly for markdown ([ai_reporter.py](ai_reporter.py)); structured evidence should come first.
- Ingest returned records with OCR, document inventory, and completeness checking.
- Add `in-depth/` and approved primary documents to ChatTDB.
- Begin packet versioning and semantic diffs.

### Days 46–90

- Publish the first Rio Nuevo approved-versus-paid ledger.
- Publish one “What They Promised” audit with timestamped receipts.
- Add a public records-responsiveness page after enough real requests exist.
- Begin entity resolution only for the narrow Rio Nuevo/data-center universe; do not attempt a metro-wide graph immediately.
- Measure impact: records released, unique facts obtained, official corrections or policy changes, documents restored, source clicks, pickups by other outlets, and requests that actually produced stories.

## Build the Tucson layer; reuse commodity infrastructure

Do not spend your time creating generic OCR, document hosting, or national agenda infrastructure. DocumentCloud already supports OCR, annotation, search, APIs, scheduled Add-Ons, and public document embeds; it is a natural primary-document layer beneath TDB’s private intelligence system. [MuckRock’s current DocumentCloud documentation](https://help.muckrock.com/DocumentCloud-19ef8892696381ee8fc4de8d62aa4704) and [Add-On system](https://help.muckrock.com/Add-Ons-19ef88926963810c9df9e46762194322) are worth evaluating.

Stanford’s Big Local News is already standardizing difficult local datasets and aggregating agendas nationally. The differentiator for TDB is not another generic agenda collector; it is the deep Tucson join across meetings, money, people, records, and outcomes. [Stanford’s description of Big Local News](https://journalism.stanford.edu/news/stanfords-big-local-news-platform-empowers-newsrooms-produce-impactful-data-journalism) also suggests a potential collaboration or data-sharing path.

The external best practice matches what your own repository has learned: AP’s Local Lede uses trusted public sources, programmatic validation, self-checks, and human oversight, while AP’s newly updated AI standards keep editorial judgment and verification with journalists. [AP Local Lede](https://www.ap.org/media-center/press-releases/2024/ap-appliedxl-to-deliver-ai-powered-news-tips-to-local-newsrooms/), [AP AI standards](https://www.ap.org/the-definitive-source/announcements/ap-updates-newsroom-standards-for-artificial-intelligence/).

The guiding principle I would use is:

> **Automate observation, comparison, memory, and verification. Keep accusation, causation, fairness, and publication with the journalist.**

You have already built the automated eyes and ears. The next consequential build is the memory—and the machinery that turns memory into receipts.
