"""Provenance gate — every proper noun in a generated brief must trace back to
the source text the model was actually given.

The synthesis prompt has told the model "NEVER fabricate names" since day one,
and on 2026-07-23 it wrote "David Barrett" anyway: the Oro Valley mayor-elect is
Melanie Barrett, and the cited KVOA source only ever said "Barrett." The model
supplied a plausible given name and had no way to know it was doing so.

Instructions can't fix that, because a confabulated fact and a recalled one feel
identical from the inside. So this is a mechanical check with no model in it:
extract every capitalized multi-word run from the draft, and confirm each one
appears verbatim in the prompt that produced it. Anything present in the output
but absent from the input was introduced during synthesis.

Three outcomes per run:

    GROUNDED    the full string is in the source text                -> pass
    PARTIAL     a shorter suffix is ("Barrett" but not "David        -> repairable:
                Barrett") — a modifier was invented                     trim to what's supported
    UNGROUNDED  no trace at all                                      -> not repairable, flag

PARTIAL is the interesting one and the case that actually bit us. Trimming
"David Barrett" to "Barrett" is a deterministic string operation that makes the
brief say less rather than guess — which is the desired behaviour.

Run modes:
    SHADOW   classify and log, return the draft untouched (start here)
    ENFORCE  additionally apply PARTIAL repairs to the returned draft

Usage:
    from provenance_gate import check, Mode
    result = check(draft_md, source_text, mode=Mode.SHADOW)
    result.findings      # every classified run
    result.suspect       # PARTIAL + UNGROUNDED only
    result.text          # SHADOW: unchanged. ENFORCE: repaired.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import re
import unicodedata
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

# Both sides of the comparison get flattened the same way, so punctuation and
# line breaks can't create a spurious mismatch. "Today: Mostly sunny" and
# "Today Mostly" both reduce to a form where one contains the other.
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(s: str) -> str:
    """Casefold, strip accents, reduce every run of non-alphanumerics to one space."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return f" {_NON_ALNUM.sub(' ', s.lower()).strip()} "


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

# Words that appear capitalized for structural reasons (sentence start, weekday,
# section header) and would otherwise glue themselves onto adjacent proper nouns.
_STRUCTURAL = frozenset("""
a an the and or but if as at by for from in into of on to with without over under
between through during after before while since until about above below out off up
down again further then once here there when where why how what which who whom whose
all any both each few more most other some such only own same so than too very can
will just should now not no nor is are was were be been being has have had do does did
this that these those it its he she they them his her their our your my we you i
monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
""".split())

# Honorifics and offices: real, but they precede the name rather than being part
# of it. Trimming them keeps "Mayor Regina Romero" from being treated as a
# three-word name that must match verbatim.
_TITLES = frozenset("""
mayor governor sheriff chief councilmember councilwoman councilman supervisor
rep sen senator congressman congresswoman treasurer superintendent attorney
judge justice director manager officer detective sergeant captain lieutenant
deputy dr mr ms mrs chairman chairwoman chair vice president secretary
""".split())

# Abbreviations whose trailing period does NOT end a sentence. Any other
# period-terminated token breaks the run, so "…David Schweikert. In Santa Cruz
# County…" yields two runs rather than one nonsense span across the boundary.
_ABBREV = frozenset("""
u.s. u.k. st. mt. ft. jr. sr. inc. co. corp. ltd. dr. ave. rd. blvd. ln. pkwy.
no. dept. gov. rep. sen. gen. col. lt. sgt. capt. det. asst. assoc. univ.
""".split())

_CAP_RUN = re.compile(r"(?:\b[A-Z][\w'’-]*\.?[ \t]+){1,}(?:\b[A-Z][\w'’-]*\.?)")

# Attribution lines (📰 / 📄) are generated against a Python-owned source list and
# validated by the existing link rules — not model claims about the world.
_ATTRIBUTION = re.compile(r"^\s*[\U0001F4F0\U0001F4C4].*$", re.M)
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_EMPH = re.compile(r"[*_`#>]+")


def _strip_markup(text: str) -> str:
    text = _ATTRIBUTION.sub(" ", text)
    text = _MD_LINK.sub(r"\1", text)     # keep link text, drop the URL
    text = re.sub(r"<[^>]+>", " ", text)
    return _MD_EMPH.sub(" ", text)


def extract_runs(text: str) -> set[str]:
    """Maximal runs of consecutive capitalized words, title/structural words trimmed.

    Multi-word runs only. A bare "Barrett" is not checkable — the interesting
    claim is always the combination ("David" + "Barrett"), never the single token.
    """
    runs: set[str] = set()
    for match in _CAP_RUN.finditer(_strip_markup(text)):
        for words in _split_sentences(match.group(0).split()):
            # Trim structural/title words from both ends, not the middle: "Vice
            # Mayor Melanie Barrett" -> "Melanie Barrett", but "Jose de la Cruz"
            # survives. "U.S. Rep. Andy Biggs" -> "Andy Biggs".
            while words and (words[0].lower() in _ABBREV
                             or words[0].lower().strip(".") in _STRUCTURAL | _TITLES):
                words = words[1:]
            while words and words[-1].lower().strip(".") in _STRUCTURAL:
                words = words[:-1]
            if words and words[-1].lower() not in _ABBREV:
                words = words[:-1] + [words[-1].rstrip(".")]   # sentence-final period
            if len(words) >= 2:
                runs.add(" ".join(words))
    return runs


def _split_sentences(words: list[str]) -> list[list[str]]:
    """Break a capitalized run wherever a token ends a sentence.

    A trailing period ends the run unless the token is a known abbreviation, so
    "Schweikert. In Santa Cruz County" splits instead of being read as one name.
    """
    out, current = [], []
    for w in words:
        current.append(w)
        if w.endswith(".") and w.lower() not in _ABBREV:
            out.append(current)
            current = []
    if current:
        out.append(current)
    return out


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

# Generic nouns that end an organisation or place name. A run ending in one of
# these is not a person, so its "supported suffix" is a common noun rather than a
# surname — trimming "Sahuarita Unified School District" to "District" is
# nonsense, where trimming "David Barrett" to "Barrett" is exactly right.
_GENERIC_TAIL = frozenset("""
road street avenue boulevard drive lane way place court circle trail highway
freeway parkway loop path bridge park plaza mall center centre district county
city town village school schools college university department division office
bureau agency board commission committee council authority foundation institute
society association alliance coalition partnership program act warning watch
advisory service services system systems network group holdings company
corporation corp inc llc ltd bank hospital health clinic church temple library
museum theater theatre stadium arena airport station campus hall house lodge
resort hotel motel market store shop restaurant bar cafe pizza brewery winery
energy construction development properties realty ranch farm valley canyon mesa
wash creek river mountain mountains peak pass springs estates heights village
day week month year edition mini brief report update fund trust project
initiative plan strategy summit conference festival fair expo tour series
business unified consolidated media news press journal times post herald
gazette tribune weekly daily magazine review spotlight
""".split())

# Spanish and civic prefixes that lead a place name. Trimmed from the left so
# "Via Entrada" and "Barrio Anita" don't read as given-name + surname.
_PLACE_PREFIX = frozenset("""
via camino calle paseo avenida plaza barrio rancho casa villa el la los las
fort mount saint san santa
""".split())


class Status(str, enum.Enum):
    GROUNDED = "grounded"
    PARTIAL = "partial"
    UNGROUNDED = "ungrounded"


class Mode(str, enum.Enum):
    SHADOW = "shadow"
    ENFORCE = "enforce"


@dataclasses.dataclass(frozen=True)
class Finding:
    run: str
    status: Status
    supported: str | None = None   # longest suffix that IS in the sources

    @property
    def dropped(self) -> str | None:
        """The unsupported prefix — the part that was invented."""
        if self.status is not Status.PARTIAL or not self.supported:
            return None
        return self.run[: len(self.run) - len(self.supported)].strip()

    @property
    def person_shaped(self) -> bool:
        """Whether this run plausibly names a human being.

        Misnaming a person is the harm worth interrupting a human for; an
        unmatched street or program name is usually a fetch-window artifact. This
        is a precision filter on *alerts* only — every finding is still logged,
        so the heuristic can be tuned against real shadow data rather than guessed
        at permanently.
        """
        words = self.run.split()
        if not 2 <= len(words) <= 3 or "'" in self.run or "’" in self.run:
            return False
        if words[-1].lower() in _GENERIC_TAIL or words[0].lower() in _PLACE_PREFIX:
            return False
        for w in words:
            if not w.isalpha() or len(w) < 2:
                return False          # initials ("James M") aren't checkable
            if w.isupper():
                return False          # acronyms ("Arizona GOP", "TMC Rincon")
            if not w[0].isupper():
                return False
        return True


@dataclasses.dataclass
class Result:
    text: str
    findings: list[Finding]
    mode: Mode
    repairs: list[tuple[str, str]] = dataclasses.field(default_factory=list)

    @property
    def suspect(self) -> list[Finding]:
        """Everything unverified — the full log, including place and org noise."""
        return [f for f in self.findings if f.status is not Status.GROUNDED]

    @property
    def alerts(self) -> list[Finding]:
        """Unverified runs that name a person — the ones worth waking someone for."""
        return [f for f in self.suspect if f.person_shaped]

    @property
    def ok(self) -> bool:
        return not self.alerts

    def summary(self) -> str:
        n = len(self.findings)
        good = n - len(self.suspect)
        parts = [f"{good}/{n} runs grounded"]
        if self.suspect:
            parts.append(
                f"{sum(f.status is Status.PARTIAL for f in self.suspect)} partial, "
                f"{sum(f.status is Status.UNGROUNDED for f in self.suspect)} ungrounded"
            )
        parts.append(f"{len(self.alerts)} person-shaped")
        if self.repairs:
            parts.append(f"{len(self.repairs)} repaired")
        return "; ".join(parts)


def classify(run: str, haystack: str) -> Finding:
    """Locate the longest suffix of `run` that appears in the source text."""
    if normalize(run).strip() in haystack:
        return Finding(run, Status.GROUNDED)

    words = run.split()
    # Walk in from the left: "David Tyrone Barrett" -> "Tyrone Barrett" -> "Barrett".
    # A surviving suffix means only the leading modifier was unsupported.
    for start in range(1, len(words)):
        suffix = " ".join(words[start:])
        if normalize(suffix).strip() in haystack:
            return Finding(run, Status.PARTIAL, supported=suffix)
    return Finding(run, Status.UNGROUNDED)


def check(draft: str, sources: str, mode: Mode = Mode.SHADOW) -> Result:
    """Classify every capitalized run in `draft` against `sources`.

    `sources` should be everything the model was given that describes the world —
    the items block, the weather block, and the editor tips — concatenated.
    """
    haystack = normalize(sources)
    findings = sorted(
        (classify(run, haystack) for run in extract_runs(draft)),
        key=lambda f: (f.status is Status.GROUNDED, f.run.lower()),
    )

    text, repairs = draft, []
    if mode is Mode.ENFORCE:
        for f in findings:
            if f.status is Status.PARTIAL and f.supported and _repairable(f):
                # Whole-word boundaries so "Barrett" can't match inside another token.
                pattern = re.compile(rf"\b{re.escape(f.run)}\b")
                if pattern.search(text):
                    text = pattern.sub(f.supported, text)
                    repairs.append((f.run, f.supported))
    return Result(text=text, findings=findings, mode=mode, repairs=repairs)


def _repairable(f: Finding) -> bool:
    """Only rewrite published prose when the edit is unambiguously safe.

    Editing a brief is riskier than flagging one, so anything with punctuation,
    initials, or non-alphabetic tokens is left alone and merely reported. A
    botched repair ("U.S. Rep. Andy Biggs" -> "U.Andy Biggs") is worse than the
    unverified name it was trying to fix.
    """
    dropped = f.dropped or ""
    return (
        bool(dropped)
        and f.person_shaped
        and len(dropped.split()) == 1              # a single invented given name
        and len((f.supported or "").split()) == 1  # leaving a bare surname
        and dropped.isalpha()
        and len(dropped) > 1
    )


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

def log_jsonl(result: Result, path, date_str: str) -> None:
    """Append one record per run. Shadow-mode data for tuning before enforcement."""
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(path, "a", encoding="utf-8") as fh:
        for f in result.suspect:
            fh.write(json.dumps({
                "logged_at": stamp,
                "brief_date": date_str,
                "mode": result.mode.value,
                "run": f.run,
                "status": f.status.value,
                "supported": f.supported,
                "dropped": f.dropped,
            }) + "\n")


if __name__ == "__main__":
    # Regression test: the failure this module exists to catch.
    SOURCES = """
    ### SOURCE: KVOA News 4
    - TITLE: Barrett with big lead in bid to become Oro Valley's next mayor
    ### SOURCE: Arizona Mirror
    - TITLE: Andy Biggs easily defeats David Schweikert, wins GOP nomination for governor
    ### SOURCE: Nogales International
    - TITLE: First-time candidate David Ruiz takes early lead for Nogales mayor
    """
    DRAFT = (
        "In Oro Valley, David Barrett won the mayoral race by a large margin. "
        "U.S. Rep. Andy Biggs defeated David Schweikert. In Santa Cruz County, "
        "David Ruiz led early. Mayor Regina Romero was not on the ballot."
    )

    res = check(DRAFT, SOURCES, mode=Mode.ENFORCE)
    print(res.summary(), "\n")
    for f in res.findings:
        mark = {"grounded": "ok  ", "partial": "PART", "ungrounded": "UNGR"}[f.status.value]
        extra = f"  -> keep {f.supported!r}, drop {f.dropped!r}" if f.dropped else ""
        print(f"  [{mark}] {f.run}{extra}")
    print("\nrepaired text:\n ", res.text)

    assert any(f.run == "David Barrett" and f.status is Status.PARTIAL for f in res.findings), \
        "the Barrett case must classify as PARTIAL"
    assert "David Barrett" not in res.text and "Barrett won" in res.text
    for good in ("David Schweikert", "David Ruiz", "Andy Biggs", "Regina Romero"):
        assert good in res.text, f"{good} must survive"
    assert not any(f.run == "David Schweikert" and f.status is not Status.GROUNDED
                   for f in res.findings), "real names must not be flagged"
    print("\nself-test passed")
