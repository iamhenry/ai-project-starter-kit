#!/usr/bin/env python3
"""Check App Store metadata lengths and keyword-field waste.

Usage: check_metadata.py --title T --subtitle S --keywords k1,k2 [--promo P]
Exit 1 if any check fails.
"""
import argparse
import re
import sys

LIMITS = {"title": 30, "subtitle": 30, "keywords": 100, "promo": 170}


def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower())}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle", required=True)
    p.add_argument("--keywords", required=True)
    p.add_argument("--promo", default="")
    a = p.parse_args()

    problems = []
    for field, limit in LIMITS.items():
        value = getattr(a, field)
        print(f"{field}: {len(value)}/{limit}")
        if len(value) > limit:
            problems.append(f"{field} is {len(value) - limit} characters over")

    if re.search(r",\s|\s,", a.keywords):
        problems.append("keywords: remove spaces around commas")
    terms = [t.strip().lower() for t in a.keywords.split(",") if t.strip()]
    seen = set()
    for t in terms:
        if t in seen:
            problems.append(f"keywords: '{t}' repeated")
        seen.add(t)

    visible = words(a.title) | words(a.subtitle)
    for t in terms:
        for w in t.split():
            if w in visible:
                problems.append(f"keywords: '{w}' already in title/subtitle")
            for base in visible | (seen - {t}):
                if w in (base + "s", base + "es"):
                    problems.append(f"keywords: '{w}' is a plural of '{base}'")

    for msg in problems:
        print("FAIL", msg)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
