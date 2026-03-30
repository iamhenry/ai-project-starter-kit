#!/usr/bin/env python3
"""
validate-aso-proposal.py — Validate an ASO proposal markdown file against config + Astro data.

Usage:
    python validate-aso-proposal.py <proposal_file> <config_file> \
        --astro-url <url> [--attempt N]

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import json
import random
import re
import sys
import urllib.error
import urllib.request


# ---------------------------------------------------------------------------
# Markdown parsers
# ---------------------------------------------------------------------------

def parse_proposed_keyword_string(md_text):
    """
    Extract the proposed keywords field value from the proposal.
    Looks for a code block immediately following an "**After" bold line.
    Returns the raw string or None.
    """
    # Match: **After (...):
    # ```
    # keyword,list,...
    # ```
    pattern = re.compile(
        r'\*\*After[^*]*\*\*:?\s*\n?```[^\n]*\n([^\n`]+)\n```',
        re.IGNORECASE,
    )
    m = pattern.search(md_text)
    if m:
        return m.group(1).strip()
    return None


def parse_evidence_table(md_text):
    """
    Parse all markdown tables that have Keyword (or Phrase) + Pop + Diff columns.
    Returns dict: lowercase_keyword -> {"pop": int, "diff": int}
    Handles multiple tables in the document.
    """
    rows = {}
    lines = md_text.split('\n')
    col_kw = col_pop = col_diff = -1
    in_table = False

    for line in lines:
        if '|' not in line:
            in_table = False
            col_kw = col_pop = col_diff = -1
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
        is_header_kw = any(h in lower for h in ('keyword', 'phrase'))
        is_header_pop = 'pop' in lower
        is_header_diff = 'diff' in lower

        if is_header_kw and is_header_pop and is_header_diff:
            col_kw = next(i for i, h in enumerate(lower) if h in ('keyword', 'phrase'))
            col_pop = next(i for i, h in enumerate(lower) if h == 'pop')
            col_diff = next(i for i, h in enumerate(lower) if h == 'diff')
            in_table = True
            continue

        if not in_table:
            continue

        # Data row
        if max(col_kw, col_pop, col_diff) >= len(cells):
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

        pop_m = re.search(r'\d+', pop_str)
        diff_m = re.search(r'\d+', diff_str)

        if kw and pop_m and diff_m:
            rows[kw] = {
                'pop': int(pop_m.group()),
                'diff': int(diff_m.group()),
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
# Astro MCP query
# ---------------------------------------------------------------------------

def query_astro(astro_url, keyword, app_id):
    """
    Query Astro MCP for keyword popularity + difficulty via JSON-RPC 2.0.
    Returns (pop, diff) as ints, or raises on error.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_rankings",
            "arguments": {
                "keyword": keyword,
                "appId": app_id,
                "store": "us",
            },
        },
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        astro_url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode('utf-8')

    response = json.loads(raw)
    result = response.get('result', {})
    content = result.get('content', [])

    pop = diff = None

    # Fallback for simpler Astro-compatible responders that return metrics directly
    if isinstance(result, dict):
        direct_pop = result.get('popularity') or result.get('pop') or result.get('Popularity')
        direct_diff = result.get('difficulty') or result.get('diff') or result.get('Difficulty')
        if direct_pop is not None and direct_diff is not None:
            return int(direct_pop), int(direct_diff)

    for item in content:
        text = item.get('text', '') if isinstance(item, dict) else str(item)

        # Try direct JSON parse
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                pop = (
                    parsed.get('popularity')
                    or parsed.get('pop')
                    or parsed.get('Popularity')
                )
                diff = (
                    parsed.get('difficulty')
                    or parsed.get('diff')
                    or parsed.get('Difficulty')
                )
                if pop is not None and diff is not None:
                    break
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: regex scan for key: value patterns
        pop_m = re.search(r'(?i)popularity[:\s]+(\d+)', text)
        diff_m = re.search(r'(?i)difficulty[:\s]+(\d+)', text)
        if pop_m:
            pop = int(pop_m.group(1))
        if diff_m:
            diff = int(diff_m.group(1))
        if pop is not None and diff is not None:
            break

    return pop, diff


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def run_checks(proposal_file, config_file, astro_url, attempt):
    with open(proposal_file, 'r', encoding='utf-8') as fh:
        md_text = fh.read()

    with open(config_file, 'r', encoding='utf-8') as fh:
        config = json.load(fh)

    # Parse proposal
    kw_string = parse_proposed_keyword_string(md_text)
    evidence_rows = parse_evidence_table(md_text)
    justified_keywords = parse_justified_keywords(md_text)

    # Config values
    max_difficulty = config.get('golden_ratio', {}).get('max_difficulty', 50)
    subtitle = config.get('current_metadata', {}).get('subtitle', '')
    app_id = str(config.get('app_id', ''))

    # Derived: proposed keyword list
    proposed_keywords = []
    if kw_string:
        proposed_keywords = [k.strip().lower() for k in kw_string.split(',') if k.strip()]

    checks = []

    # ------------------------------------------------------------------
    # Check 1: Proposed keyword string char count <= 100
    # ------------------------------------------------------------------
    if kw_string is None:
        checks.append({
            "name": "keyword_string_length",
            "pass": False,
            "detail": "Could not find proposed keyword string (expected a code block after '**After')",
        })
    else:
        char_count = len(kw_string)
        ok = char_count <= 100
        checks.append({
            "name": "keyword_string_length",
            "pass": ok,
            "detail": (
                f"Keyword string is {char_count}/100 chars — ok"
                if ok
                else f"Keyword string is {char_count} chars — EXCEEDS 100 char limit"
            ),
        })

    # ------------------------------------------------------------------
    # Check 2: No subtitle words duplicated in keywords field
    # ------------------------------------------------------------------
    subtitle_words = {w.lower() for w in re.split(r'\W+', subtitle) if w}
    duplicates = []
    for kw in proposed_keywords:
        for token in re.split(r'\W+', kw):
            if token and token in subtitle_words:
                duplicates.append(f"'{kw}' contains subtitle word '{token}'")

    ok = len(duplicates) == 0
    checks.append({
        "name": "no_subtitle_duplicates",
        "pass": ok,
        "detail": (
            f"No subtitle word duplicates found (subtitle: '{subtitle}')"
            if ok
            else f"Subtitle duplicates detected — {'; '.join(duplicates)}"
        ),
    })

    # ------------------------------------------------------------------
    # Check 3: Every proposed keyword has a Pop/Diff row in evidence table
    # ------------------------------------------------------------------
    missing_evidence = [kw for kw in proposed_keywords if kw not in evidence_rows]
    ok = len(missing_evidence) == 0
    checks.append({
        "name": "evidence_coverage",
        "pass": ok,
        "detail": (
            f"All {len(proposed_keywords)} proposed keywords have evidence rows"
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
    # Check 5: Spot-check 5 random keywords against Astro (±3 tolerance)
    # ------------------------------------------------------------------
    all_kws = list(proposed_keywords)
    sample_size = min(5, len(all_kws))
    rng = random.Random(0)
    sample = rng.sample(all_kws, sample_size) if all_kws else []

    mismatches = []
    errors = []

    for kw in sample:
        expected_pop = evidence_rows[kw]['pop']
        expected_diff = evidence_rows[kw]['diff']

        try:
            actual_pop, actual_diff = query_astro(astro_url, kw, app_id)

            if actual_pop is None or actual_diff is None:
                errors.append(f"'{kw}': Astro response did not contain Pop/Diff")
                continue

            actual_pop = int(actual_pop)
            actual_diff = int(actual_diff)
            pop_ok = abs(actual_pop - expected_pop) <= 3
            diff_ok = abs(actual_diff - expected_diff) <= 3

            if not pop_ok or not diff_ok:
                mismatches.append(
                    f"'{kw}': proposal Pop={expected_pop}/Diff={expected_diff}, "
                    f"Astro Pop={actual_pop}/Diff={actual_diff}"
                )
        except urllib.error.URLError as exc:
            errors.append(f"'{kw}': Astro request failed ({exc})")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"'{kw}': {type(exc).__name__}: {exc}")

    if not sample:
        ok = False
        detail = "No evidence rows found to spot-check"
    elif mismatches:
        ok = False
        checked_ok = sample_size - len(mismatches) - len(errors)
        detail = (
            f"Spot-checked {sample_size} keywords — "
            f"{checked_ok} ok, {len(mismatches)} mismatch(es) (tolerance ±3): "
            + '; '.join(mismatches)
        )
        if errors:
            detail += f"; errors: {'; '.join(errors)}"
    elif errors:
        ok = False
        detail = f"Astro verification failed for {len(errors)}/{sample_size} keyword(s): {'; '.join(errors)}"
    else:
        ok = True
        detail = f"Spot-checked {sample_size} keywords — all within ±3 tolerance"

    checks.append({
        "name": "astro_spot_check",
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
        description='Validate an ASO proposal markdown file against config and Astro data.',
    )
    parser.add_argument('proposal_file', help='Path to the proposal markdown file')
    parser.add_argument('config_file', help='Path to the config JSON file')
    parser.add_argument(
        '--astro-url',
        required=True,
        help='Astro MCP endpoint URL (e.g. http://127.0.0.1:8089/mcp)',
    )
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
        args.astro_url,
        args.attempt,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
