"""
check_wp_years.py — Sanity-check citation years in CV WP/DP entries.

For working papers and discussion papers the correct year is whatever year
appears in the series identifier (e.g. ORU WP 2026:2 → 2026), NOT the year
the draft was written. Published papers are excluded from the check because
their year comes from the journal acceptance date.

Run: python check_wp_years.py
"""

import re
from pathlib import Path

CV_FILES = [
    "Lodefalk_CV.tex",
    "Lodefalk_CV_Short.tex",
    "Lodefalk_CV_Comprehensive.tex",
]

# Regex for the citation year: the (YYYY) right after author names
RE_CITE_YEAR = re.compile(r'\((\d{4})\),')

# Checkable series: pattern → label, year-group index
SERIES_PATTERNS = [
    # ORU: "Working Paper 2026:2" or "Örebro WP 2026:2"
    (re.compile(r'Working Paper (\d{4}):\d+'), "ORU WP"),
    # RFBerlin: "Discussion Paper 089/26" → 20YY
    (re.compile(r'RFBerlin.*?Discussion Paper \d+/(\d{2})'), "RFBerlin DP"),
    # GLO: "GLO Discussion Paper \d+, (\d{4})" — GLO sometimes has year
    # GLO numbers don't embed the year, so skip
]

# Series names whose entries should be checked (others may lack embedded year)
WP_KEYWORDS = re.compile(
    r'Working Paper|Discussion Paper|Preprint|NBER WP|IZA DP|GLO DP',
    re.IGNORECASE
)

# Published-paper markers: if a \publication line contains any of these
# journal-like patterns, skip the year check
PUBLISHED_MARKERS = re.compile(
    r'\\textit\{(?!Under review|In revision|Resubmitted|Forthcoming)'
    r'(?!R&R|Revise)(?:[A-Z][^}]+Journal|Review of|Econom|Labour|Research Policy'
    r'|Economic Letters|Applied Economics|World Economy|Industrial|'
    r'Journal of|Review of Economics|Quarterly Journal)\}',
    re.IGNORECASE
)

def extract_pub_year(line: str) -> str | None:
    m = RE_CITE_YEAR.search(line)
    return m.group(1) if m else None

def check_file(path: Path) -> list[dict]:
    issues = []
    text = path.read_text(encoding="utf-8")

    for line in text.splitlines():
        if r"\publication" not in line:
            continue
        # Skip if looks like a published paper (has a journal in \textit{})
        if PUBLISHED_MARKERS.search(line):
            continue
        # Only flag lines that mention a WP/DP series
        if not WP_KEYWORDS.search(line):
            continue

        cite_year = extract_pub_year(line)
        if not cite_year:
            continue

        for pattern, label in SERIES_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            raw = m.group(1)
            series_year = f"20{raw}" if len(raw) == 2 else raw
            # Only flag when citation year is BEFORE series year — that's
            # impossible (the WP didn't exist yet). Citation year after the
            # series year is fine (e.g. citing by the most recent IZA version).
            if int(cite_year) < int(series_year):
                issues.append({
                    "file": path.name,
                    "label": label,
                    "cite_year": cite_year,
                    "series_year": series_year,
                    "snippet": line[line.index(r"\publication"):line.index(r"\publication") + 120] + "…",
                })

    return issues

def main():
    here = Path(__file__).parent
    all_issues = []
    for fname in CV_FILES:
        p = here / fname
        if not p.exists():
            print(f"  [skip] {fname} not found")
            continue
        all_issues.extend(check_file(p))

    if not all_issues:
        print("OK — no year mismatches found in WP/DP entries.")
        return

    print(f"YEAR MISMATCH — {len(all_issues)} issue(s) found:\n")
    for iss in all_issues:
        print(f"  {iss['file']}  [{iss['label']}]")
        print(f"    Citation year : {iss['cite_year']}")
        print(f"    Series year   : {iss['series_year']}")
        print(f"    Entry         : {iss['snippet']}")
        print()

if __name__ == "__main__":
    main()
