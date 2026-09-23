#!/usr/bin/env python3
"""
validate-aso-proposal.py — Validate an ASO proposal markdown file against config.

Usage:
    python validate-aso-proposal.py <proposal_file> <config_file> [--attempt N]

The main worker gathers live Astro metrics; the plan reviewer checks its captured evidence and product fit without rerunning research.

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import json
import re
import sys


# ---------------------------------------------------------------------------
# Markdown parsers
# ---------------------------------------------------------------------------

def parse_proposed_keyword_string(md_text):
    """Return the exact Keywords value from the approval table, if present."""
    return parse_approval_fields(md_text).get('keywords', (None, None))[0]


def parse_approval_fields(md_text):
    fields = {}
    for match in re.finditer(r'^\|\s*(Title|Subtitle|Keywords)\s*\|[^\n]*$', md_text, re.IGNORECASE | re.MULTILINE):
        cells = [cell.strip().strip('`') for cell in match.group().strip('|').split('|')]
        if len(cells) >= 4:
            fields[cells[0].lower()] = (cells[2], cells[3])
    return fields


def parse_evidence_table(md_text):
    """
    Parse keyword decision tables with Keyword + Pop + Diff columns.
    Returns dict: lowercase_keyword -> {"pop": int, "diff": int, "decision": str}
    Handles multiple decision tables in the document.
    """
    rows = {}
    lines = md_text.split('\n')
    col_kw = col_pop = col_diff = col_decision = -1
    in_table = False

    for line in lines:
        if '|' not in line:
            in_table = False
            col_kw = col_pop = col_diff = col_decision = -1
            continue

        # Split and strip cells, removing empty outer cells from leading/trailing |
        raw_cells = line.split('|')
        cells = [c.strip() for c in raw_cells]
        # Remove first and last if they're empty (standard markdown table)
        if cells and cells[0] == '':
            cells = cells[1:]
        if cells and cells[-1] == '':
            cells = cells[:-1]

        if not cells:
            continue

        # Separator row (e.g. |---|---|---|)
        if re.match(r'^[-: ]+$', cells[0]):
            continue

        lower = [c.lower() for c in cells]

        # Check for header row with our expected columns
        is_header_kw = any(h in lower for h in ('keyword', 'phrase', 'keyword or phrase'))
        is_header_pop = any(h in lower for h in ('pop', 'popularity'))
        is_header_diff = any(h in lower for h in ('diff', 'difficulty'))

        if is_header_kw and is_header_pop and is_header_diff and 'decision' in lower and 'rationale' in lower:
            col_kw = next(i for i, h in enumerate(lower) if h in ('keyword', 'phrase', 'keyword or phrase'))
            col_pop = next(i for i, h in enumerate(lower) if h in ('pop', 'popularity'))
            col_diff = next(i for i, h in enumerate(lower) if h in ('diff', 'difficulty'))
            col_decision = lower.index('decision')
            in_table = True
            continue

        if not in_table:
            continue

        # Data row
        if max(col_kw, col_pop, col_diff, col_decision) >= len(cells):
            continue

        raw_kw = cells[col_kw]
        # Strip bold markers, emoji, and leading/trailing punctuation
        kw = re.sub(r'\*+', '', raw_kw).strip().lower()
        # Remove trailing parenthetical (e.g. "keyword (49)")
        kw = re.sub(r'\s*\(\d+\)\s*$', '', kw).strip()
        # Strip ⚠️ and similar
        kw = re.sub(r'[^\w,\- ]+', '', kw).strip()

        pop_str = cells[col_pop]
        diff_str = cells[col_diff]

        pop_m = re.fullmatch(r'\d+', pop_str)
        diff_m = re.fullmatch(r'\d+', diff_str)

        if kw and pop_m and diff_m:
            rows[kw] = {
                'pop': int(pop_m.group()),
                'diff': int(diff_m.group()),
                'decision': cells[col_decision].lower(),
            }

    return rows


def parse_justified_keywords(md_text):
    """
    Parse the 'Keywords Above max_difficulty' table to find which keywords
    have explicit justification text in the proposal.
    Returns a set of lowercase keyword strings.
    """
    justified = set()

    # Find the section
    section_m = re.search(
        r'###\s+Keywords Above max_difficulty[^\n]*\n(.*?)(?=\n###|\n##|\Z)',
        md_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not section_m:
        return justified

    section = section_m.group(1)

    for line in section.split('\n'):
        if '|' not in line:
            continue
        raw_cells = line.split('|')
        cells = [c.strip() for c in raw_cells]
        if cells and cells[0] == '':
            cells = cells[1:]
        if cells and cells[-1] == '':
            cells = cells[:-1]
        if not cells:
            continue
        # Skip header/separator rows
        if re.match(r'^[-: ]+$', cells[0]):
            continue
        first_lower = cells[0].lower()
        if 'keyword' in first_lower or 'phrase' in first_lower:
            continue

        # Extract keyword from first cell (strip parenthetical diff)
        kw_raw = cells[0]
        kw = re.sub(r'\*+', '', kw_raw).strip().lower()
        kw = re.sub(r'\s*\(\d+\)\s*$', '', kw).strip()
        kw = re.sub(r'[^\w,\- ]+', '', kw).strip()

        # Check if any subsequent cell has meaningful justification text
        justification_text = ' '.join(cells[1:]).strip()
        if kw and justification_text and len(justification_text) > 8:
            # Exclude if it looks like a separator or a pure number
            if not re.match(r'^[\d\s\-|:]+$', justification_text):
                justified.add(kw)

    return justified


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def run_checks(proposal_file, config_file, attempt):
    with open(proposal_file, 'r', encoding='utf-8') as fh:
        md_text = fh.read()

    with open(config_file, 'r', encoding='utf-8') as fh:
        config = json.load(fh)

    # Parse proposal
    kw_string = parse_proposed_keyword_string(md_text)
    fields = parse_approval_fields(md_text)
    evidence_rows = parse_evidence_table(md_text)
    justified_keywords = parse_justified_keywords(md_text)

    # Config values
    max_difficulty = config.get('golden_ratio', {}).get('max_difficulty', 50)
    visible = {
        word.lower()
        for field in ('title', 'subtitle')
        for word in re.split(r'\W+', fields.get(field, ('', ''))[0])
        if word
    }

    # Derived: proposed keyword list
    proposed_keywords = []
    if kw_string:
        proposed_keywords = [k.strip().lower() for k in kw_string.split(',') if k.strip()]

    checks = []

    # ------------------------------------------------------------------
    # Check 1: Exact proposed fields fit and displayed lengths agree
    # ------------------------------------------------------------------
    if kw_string is None:
        checks.append({
            "name": "metadata_lengths",
            "pass": False,
            "detail": "Could not find proposed Keywords row in approval table",
        })
    else:
        char_count = len(kw_string)
        wrong = []
        for name, limit in (('title', 30), ('subtitle', 30), ('keywords', 100)):
            if name not in fields:
                wrong.append(f"{name} row missing")
                continue
            value, stated = fields[name]
            if len(value) > limit or stated != f"{len(value)}/{limit}":
                wrong.append(f"{name}: expected {len(value)}/{limit}, found {stated}")
        if ' ' in kw_string or not kw_string:
            wrong.append("hidden keywords must be nonempty and space-free")
        ok = not wrong and char_count <= 100
        checks.append({
            "name": "metadata_lengths",
            "pass": ok,
            "detail": (
                f"Title, subtitle, keywords and displayed lengths valid ({char_count}/100 hidden chars)"
                if ok
                else '; '.join(wrong) or f"Keyword string is {char_count} chars — EXCEEDS 100 char limit"
            ),
        })

    # ------------------------------------------------------------------
    # Check 2: No proposed title/subtitle words duplicated in keywords field
    # ------------------------------------------------------------------
    duplicates = []
    for kw in proposed_keywords:
        for token in re.split(r'\W+', kw):
            if token and token in visible:
                duplicates.append(f"'{kw}' repeats visible word '{token}'")

    ok = len(duplicates) == 0
    checks.append({
        "name": "no_visible_duplicates",
        "pass": ok,
        "detail": (
            "No proposed title/subtitle word duplicates found"
            if ok
            else f"Visible word duplicates detected — {'; '.join(duplicates)}"
        ),
    })

    # ------------------------------------------------------------------
    # Check 3: Every selected hidden token and visible phrase has Pop/Diff
    # ------------------------------------------------------------------
    missing_evidence = [kw for kw in proposed_keywords if kw not in evidence_rows]
    for field in ('title', 'subtitle'):
        value = fields.get(field, ('', ''))[0]
        visible_text = re.sub(r'[^\w]+', ' ', value.lower()).strip()
        if not any(
            row['decision'] == field
            and f" {re.sub(r'[^\w]+', ' ', phrase).strip()} " in f" {visible_text} "
            for phrase, row in evidence_rows.items()
        ):
            missing_evidence.append(f"{field} phrase")
    ok = len(missing_evidence) == 0
    checks.append({
        "name": "evidence_coverage",
        "pass": ok,
        "detail": (
            "Selected title/subtitle phrases and hidden keywords have numeric evidence"
            if ok
            else f"Missing evidence for {len(missing_evidence)} keyword(s): {', '.join(missing_evidence)}"
        ),
    })

    # ------------------------------------------------------------------
    # Check 4: Keywords above max_difficulty have justification
    # ------------------------------------------------------------------
    unjustified = []
    for kw in proposed_keywords:
        if kw in evidence_rows and evidence_rows[kw]['diff'] > max_difficulty:
            if kw not in justified_keywords:
                unjustified.append(f"{kw} (Diff={evidence_rows[kw]['diff']})")

    ok = len(unjustified) == 0
    checks.append({
        "name": "high_difficulty_justified",
        "pass": ok,
        "detail": (
            f"All keywords above max_difficulty={max_difficulty} are explicitly justified"
            if ok
            else (
                f"Missing justification for {len(unjustified)} keyword(s) "
                f"above max_difficulty={max_difficulty}: {', '.join(unjustified)}"
            )
        ),
    })

    # ------------------------------------------------------------------
    # Check 5: Approval table and candidate decision table are present
    # ------------------------------------------------------------------
    decisions = re.search(
        r'^\|\s*Keyword or phrase\s*\|\s*Pop\s*\|\s*Diff\s*\|\s*Decision\s*\|\s*Rationale\s*\|\s*Evidence\s*\|',
        md_text, re.IGNORECASE | re.MULTILINE,
    )
    ok = bool(decisions and '## Approval view' in md_text and evidence_rows)
    detail = "Approval and keyword-decision tables present" if ok else "Missing approval or keyword-decision table"

    checks.append({
        "name": "decision_table",
        "pass": ok,
        "detail": detail,
    })

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------
    overall_pass = all(c['pass'] for c in checks)
    return {
        "pass": overall_pass,
        "checks": checks,
        "attempt": attempt,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Validate ASO proposal structure and numeric evidence against config.',
    )
    parser.add_argument('proposal_file', help='Path to the proposal markdown file')
    parser.add_argument('config_file', help='Path to the config JSON file')
    parser.add_argument(
        '--attempt',
        type=int,
        default=1,
        help='Attempt number for tracking retries (default: 1)',
    )

    args = parser.parse_args()

    result = run_checks(
        args.proposal_file,
        args.config_file,
        args.attempt,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
