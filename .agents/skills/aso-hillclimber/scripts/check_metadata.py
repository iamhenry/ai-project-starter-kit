#!/usr/bin/env python3
"""Check App Store metadata lengths and keyword-field waste.

Usage: check_metadata.py --title T --subtitle S --keywords k1,k2 [--promo P]
Exit 1 if any check fails.
"""
import argparse
import json
import re
import sys
from collections import Counter

LIMITS = {"title": 30, "subtitle": 30, "keywords": 100, "promo": 170}


def words(text):
    return set(re.findall(r"[^\W_]+", text.casefold(), re.UNICODE))


def check_listings(path, popularity_path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    popularity = None
    if popularity_path:
        with open(popularity_path, encoding="utf-8") as f:
            popularity = json.load(f)
    listings = data["listings"]
    errors = []
    warnings = []
    for locale, listing in listings.items():
        for field in ("title", "subtitle", "keywords"):
            length = len(listing[field])
            print(f"{locale} {field}: {length}/{LIMITS[field]}")
            if length > LIMITS[field]:
                errors.append(f"{locale}: {field} exceeds {LIMITS[field]}")
        keywords = words(listing["keywords"])
        for banned in ["app", *data.get("app_names", []),
                       *data.get("company_names", []), *data.get("categories", []),
                       *data.get("missing_features", [])]:
            if words(banned) and words(banned) <= keywords:
                errors.append(f"{locale}: keywords contain '{banned}'")
        if re.search(r",\s|\s,", listing["keywords"]):
            errors.append(f"{locale}: remove spaces around commas")

    for store, locales in data["storefronts"].items():
        tokens = []
        for locale in locales:
            listing = listings[locale]
            for field in ("title", "subtitle", "keywords"):
                tokens.extend(re.findall(r"[^\W_]+", listing[field].casefold(), re.UNICODE))
        counts = Counter(tokens)
        for word, count in sorted(counts.items()):
            if count > 1:
                errors.append(f"{store}: '{word}' repeated {count} times")
            for base in counts:
                if word != base and word in (base + "s", base + "es"):
                    warnings.append(f"{store}: '{word}' may be a plural of '{base}'")
        if popularity is not None:
            for target in data.get("targets", {}).get(store, []):
                score = popularity.get(store, {}).get(target)
                if score is None or score < 20:
                    errors.append(f"{store}: target '{target}' popularity {score} (minimum 20)")
    for msg in warnings:
        print("WARN", msg)
    for msg in errors:
        print("FAIL", msg)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return bool(errors)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--keywords")
    p.add_argument("--promo", default="")
    p.add_argument("--listings", help="JSON file with listings and storefront-to-locale mapping")
    p.add_argument("--popularity", help="JSON file mapping storefronts to target popularity")
    a = p.parse_args()
    if a.listings:
        try:
            sys.exit(check_listings(a.listings, a.popularity))
        except (OSError, ValueError, KeyError, TypeError) as e:
            p.error(str(e))
    if any(v is None for v in (a.title, a.subtitle, a.keywords)):
        p.error("--title, --subtitle and --keywords are required without --listings")

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
