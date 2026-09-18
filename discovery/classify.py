"""Stage 2 of discovery: decide which candidate URLs are real scheme pages.

Pure heuristics. No LLM call is made here, which is the whole point: this
stage exists to stop the extractor from spending quota on tender notices,
recruitment ads and department landing pages.

Scoring is additive and transparent. Every page carries its signal list into
the output, so a later trust score can cite why a page was accepted.

    python classify.py --in candidates.jsonl --out classified.jsonl
    python classify.py --in candidates.jsonl --out kept.jsonl --min-score 0.55
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

from fetcher import PoliteFetcher

# Positive signals: (name, weight, regex). Matched against the page text.
POSITIVE = [
    ("eligibility", 0.28, r"\beligib(le|ility)\b|\bwho\s+can\s+apply\b|\bqualif(y|ying)\b"),
    ("benefits", 0.20, r"\bbenefit(s)?\b|\bassistance\b|\bfinancial\s+support\b|\bincentive\b"),
    ("how_to_apply", 0.18, r"\bhow\s+to\s+apply\b|\bapplication\s+(process|procedure|form)\b"),
    ("documents", 0.12, r"\bdocuments?\s+required\b|\brequired\s+documents?\b|\benclosures?\b"),
    ("scheme_word", 0.10, r"\bscheme\b|\byojana\b|\byojna\b|\bthittam\b|\bmission\b"),
    ("authority", 0.08, r"\bministry\s+of\b|\bdepartment\s+of\b|\bgovernment\s+of\b|\bdirectorate\b"),
    ("money_figure", 0.08, r"(rs\.?|₹|inr)\s?[\d,]{3,}|\blakh\b|\bcrore\b|\bper\s+annum\b"),
    ("beneficiary", 0.06, r"\bbeneficiar(y|ies)\b|\bapplicant\b|\btarget\s+group\b"),
]

# Negative signals: page is something else wearing a scheme-ish URL.
NEGATIVE = [
    ("tender", 0.45, r"\btender\b|\bbid\s+document\b|\bearnest\s+money\b|\bemd\b"),
    ("recruitment", 0.45, r"\brecruitment\b|\bvacanc(y|ies)\b|\bwalk[- ]in\s+interview\b"),
    ("press_release", 0.25, r"\bpress\s+(release|information\s+bureau)\b|\bposted\s+on:\b"),
    ("listing_page", 0.20, r"\bsearch\s+results\b|\bshowing\s+\d+\s+of\s+\d+\b|\bfilter\s+by\b"),
    ("login_wall", 0.35, r"\bsign\s+in\b.*\bpassword\b|\bcaptcha\b|\bforgot\s+password\b"),
    ("error_page", 0.60, r"\bpage\s+not\s+found\b|\b404\b\s*error|\baccess\s+denied\b"),
]

MIN_TEXT_CHARS = 400
MAX_TEXT_CHARS = 120_000


@dataclass
class Verdict:
    score: float
    is_scheme: bool
    signals: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    title: str = ""
    text_chars: int = 0
    reason: str = ""


def extract_text(html: str) -> tuple[str, str]:
    """Return (title, visible text) with script/style/nav chrome removed."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        tag.decompose()
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    if soup.head is not None:
        soup.head.decompose()  # otherwise <title> is counted twice, in title and text
    text = re.sub(r"\s+", " ", soup.get_text(" "))
    return title, text.strip()


def score_page(title: str, text: str, url: str = "", threshold: float = 0.55) -> Verdict:
    """Score one page. Pure function - no network, fully unit-testable."""
    blob = f"{title} {text}".lower()
    chars = len(text)

    if chars < MIN_TEXT_CHARS:
        return Verdict(0.0, False, title=title, text_chars=chars, reason="too_short")
    if chars > MAX_TEXT_CHARS:
        return Verdict(0.0, False, title=title, text_chars=chars, reason="too_long")

    score = 0.0
    signals: list[str] = []
    for name, weight, pattern in POSITIVE:
        if re.search(pattern, blob):
            score += weight
            signals.append(name)

    penalties: list[str] = []
    for name, weight, pattern in NEGATIVE:
        if re.search(pattern, blob):
            score -= weight
            penalties.append(name)

    # A page with benefits and money but no eligibility text is a brochure,
    # not something the eligibility engine can ever evaluate against.
    if "eligibility" not in signals:
        score -= 0.15
        penalties.append("no_eligibility_section")

    score = max(0.0, min(1.0, score))
    reason = "accepted" if score >= threshold else "below_threshold"
    return Verdict(
        score=round(score, 3),
        is_scheme=score >= threshold,
        signals=signals,
        penalties=penalties,
        title=title,
        text_chars=chars,
        reason=reason,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Classify candidate scheme URLs.")
    ap.add_argument("--in", dest="infile", default="candidates.jsonl")
    ap.add_argument("--out", default="classified.jsonl")
    ap.add_argument("--min-score", type=float, default=0.55)
    ap.add_argument("--limit", type=int, help="stop after N candidates")
    ap.add_argument("--keep-only", action="store_true", help="write accepted pages only")
    ap.add_argument("--cache", default=".cache/discovery")
    args = ap.parse_args()

    lines = [l for l in Path(args.infile).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        lines = lines[: args.limit]

    kept = 0
    out_path = Path(args.out)

    with PoliteFetcher(cache_dir=Path(args.cache)) as fetcher:
        with out_path.open("w", encoding="utf-8") as fh:
            for i, line in enumerate(lines, 1):
                cand = json.loads(line)
                result = fetcher.get(cand["url"])
                if result is None:
                    record = {**cand, "score": 0.0, "is_scheme": False, "reason": "blocked_or_failed"}
                elif not result.ok:
                    record = {**cand, "score": 0.0, "is_scheme": False, "reason": f"http_{result.status}"}
                else:
                    title, text = extract_text(result.text)
                    v = score_page(title, text, cand["url"], threshold=args.min_score)
                    record = {**cand, **v.__dict__}
                    record["signals"] = v.signals
                    record["penalties"] = v.penalties

                if record.get("is_scheme"):
                    kept += 1
                if args.keep_only and not record.get("is_scheme"):
                    continue

                # Write per item, so an interrupted run keeps its progress.
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                fh.flush()

                if i % 25 == 0:
                    print(f"[classify] {i}/{len(lines)} checked, {kept} accepted", flush=True)

    print(f"[classify] done: {kept} accepted of {len(lines)} -> {out_path}")


if __name__ == "__main__":
    main()
