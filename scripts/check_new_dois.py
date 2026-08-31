#!/usr/bin/env python3
"""Report published work that carries a DOI but does not appear on the CV.

WHY THIS EXISTS. Nothing keeps the CV current: its content is edited by hand, and only the
compile-and-publish step is automated. The change that most often goes unrecorded is a working
paper becoming a journal article, because it happens on the journal's schedule rather than on
Magnus's. There is a monthly LLM routine that audits the CV more broadly, but it runs on a
bridge environment that has silently died before and needs his Mac awake. This script is the
floor beneath it: no model, no bridge, no laptop, and it fails loudly on a GitHub runner.

WHAT IT IS NOT. It is a detector, not an audit. It sees only works that OpenAlex has linked to
the ORCID and that carry a real DOI, so it is silent about accepted-but-unpublished papers,
grants, presentations, and anything published without the ORCID attached at submission. A clean
run means "no new DOI", never "the CV is complete".

DISAMBIGUATION. Matching is by ORCID, never by surname. Maria Lodefalk is a paediatric
endocrinologist at the same university who publishes frequently; a name search returns her work
in every query, and it is not his.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

ORCID = "0000-0003-0149-9598"
CONTACT = "mlodefalk@gmail.com"          # OpenAlex asks for a contact; it buys the polite pool
CV_FILES = ["Lodefalk_CV_Short.tex", "Lodefalk_CV.tex", "Lodefalk_CV_Comprehensive.tex"]

# Prefixes that are not publications. SSRN and RePEc mint DOIs for working papers, which sit
# on the CV in the working-papers section cited by series number rather than DOI; ResearchGate
# and AgEcon mint DOIs for uploads. Reporting any of them would fire every single run.
# OpenAlex's own type is filtered too: neither alone is enough, because it labels some of these
# "article".
NON_PUBLICATION_PREFIXES = (
    "10.2139/ssrn",       # SSRN
    "10.48550/arxiv",     # arXiv
    "10.31219/osf",       # OSF preprints
    "10.13140/rg",        # ResearchGate uploads
    "10.22004/ag.econ",   # AgEcon Search
)
SKIP_TYPES = {"preprint"}

# Matching on DOI alone is not enough, for two reasons found on the first real run.
# Inderscience mints two DOIs per article, an in-press one and a final-issue one, so the IJESB
# paper looked missing while sitting on the CV under its other DOI. And a paper reprinted as a
# book chapter gets a second DOI for the chapter, which is how the 2007 World Economy article
# reappeared as a Wiley chapter. Both are the same work, already recorded. So the title is
# checked as a second key: if the CV already names the paper, it is not new, whatever DOI
# OpenAlex attached to this copy of it.
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
LATEX_RE = re.compile(r"\\[a-zA-Z]+|[{}$\\]")
NONWORD_RE = re.compile(r"[^a-z0-9 ]+")


def normalise(s: str) -> str:
    """Lowercase, strip LaTeX and punctuation, collapse whitespace."""
    s = LATEX_RE.sub(" ", s)
    return " ".join(NONWORD_RE.sub(" ", s.lower()).split())


def read_cv(root: Path) -> tuple[set[str], str]:
    """Return the DOIs the CV cites, and its whole text normalised for title matching."""
    dois, text = set(), []
    for name in CV_FILES:
        path = root / name
        if not path.exists():
            sys.exit(f"error: {path} not found; run this from the cv repository")
        raw = path.read_text(encoding="utf-8")
        for m in DOI_RE.finditer(raw):
            # \href{https://doi.org/10.x/y}{...} leaves a trailing brace on the match
            dois.add(m.group(0).rstrip("}").rstrip(".,;").lower())
        text.append(normalise(raw))
    return dois, " ".join(text)


def works_from_openalex() -> list[dict]:
    url = (f"https://api.openalex.org/works?filter=author.orcid:{ORCID}"
           f"&per-page=200&mailto={CONTACT}")
    req = urllib.request.Request(url, headers={"User-Agent": f"cv-doi-check ({CONTACT})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["results"]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    on_cv, cv_text = read_cv(root)

    try:
        works = works_from_openalex()
    except Exception as e:                      # noqa: BLE001 - any failure is worth reporting
        print(f"error: could not reach OpenAlex: {e}", file=sys.stderr)
        return 2

    missing = []
    for w in works:
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        if not doi or doi in on_cv:
            continue
        if w.get("type") in SKIP_TYPES or doi.startswith(NON_PUBLICATION_PREFIXES):
            continue
        title = normalise(w.get("title") or "")
        if len(title) > 25 and title in cv_text:
            continue        # already on the CV under another DOI, or as another version
        missing.append({
            "doi": doi,
            "title": (w.get("title") or "").strip(),
            "year": w.get("publication_year"),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            "type": w.get("type"),
        })

    missing.sort(key=lambda m: (-(m["year"] or 0), m["title"]))

    print(f"OpenAlex works under ORCID {ORCID}: {len(works)}")
    print(f"DOIs already cited on the CV: {len(on_cv)}")
    print(f"Published DOIs not on the CV: {len(missing)}")
    if not missing:
        return 0

    print()
    for m in missing:
        venue = m["venue"] or "venue not stated by OpenAlex"
        print(f"- {m['year']} · {m['title']}")
        print(f"  {venue} · https://doi.org/{m['doi']} · OpenAlex type: {m['type']}")
    print()
    print("Verify each against the journal's own page before adding it: OpenAlex metadata is "
          "aggregated and its volume, issue and page fields are not always right. Then run "
          "/cv in Claude Code with the accomplishment.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
