#!/usr/bin/env python3
"""Bounded HTTP retry helper retained for Clef's direct first-pass request."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import random
import sys
import time
import urllib.error
import urllib.request


MAX_ATTEMPTS = 5
BACKOFF_SECONDS = 30
MAX_BACKOFF_SECONDS = 600


class RateLimitError(RuntimeError):
    """A retryable HTTP response persisted through the bounded retry window."""

    def __init__(self, status, attempts):
        self.status = status
        self.attempts = attempts
        super().__init__(f"HTTP {status} after {attempts} attempts")


def retry_after_seconds(value):
    if not value:
        return None
    try:
        seconds = float(value)
        return max(0, seconds) if math.isfinite(seconds) else None
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return max(0, (when - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def request_with_retry(request, timeout=600):
    """Retry rate-limit/server responses without changing the judge client API."""
    for attempt in range(MAX_ATTEMPTS):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status != 429 and not 500 <= status < 600:
                raise
            delay = retry_after_seconds(exc.headers.get("Retry-After"))
            exc.close()
            if delay is not None and delay > MAX_BACKOFF_SECONDS:
                raise RateLimitError(status, attempt + 1) from None
            if attempt + 1 == MAX_ATTEMPTS:
                raise RateLimitError(status, MAX_ATTEMPTS) from None
            if delay is None:
                backoff = min(MAX_BACKOFF_SECONDS, BACKOFF_SECONDS * (2 ** attempt))
                delay = min(MAX_BACKOFF_SECONDS, backoff + random.uniform(0, min(10, backoff * 0.1)))
            print(f"HTTP {status}; retry {attempt + 2}/{MAX_ATTEMPTS} in {delay:.1f}s", file=sys.stderr)
            time.sleep(delay)
