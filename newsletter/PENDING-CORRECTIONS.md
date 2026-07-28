# Pending corrections for TDB Weekly

Corrections waiting to be pasted into the next newsletter draft by hand.
`generate_newsletter.py` has no manual-insert hook, so this is a review-time step:
after generating the draft, before `upload_to_buttondown.py`.

Delete an entry once it has actually sent.

---

## For the send on Sunday, 2026-08-02

**Placement:** fold into the opening paragraph, before `## What's worth knowing`.

```markdown
One housekeeping note before we start: last week I named the winner of the
Oro Valley mayor's race as David Barrett. It's **Melanie Barrett**, the
town's vice mayor, who won 57–43 over Mark Napier. My error, now fixed on
the site. Apologies to Mayor-elect Barrett.
```

**Background:** the 2026-07-26 newsletter and the 2026-07-23 daily brief both
named the Oro Valley mayor-elect as "David Barrett." The winner is Melanie
Barrett (Vice Mayor), who defeated former Pima County Sheriff Mark Napier
57–43. The cited KVOA source named her correctly — the given name was
introduced during synthesis and appeared in no source. The daily brief was
corrected in place on 2026-07-28 (commit `02c60de`); the newsletter had
already sent and cannot be recalled.
