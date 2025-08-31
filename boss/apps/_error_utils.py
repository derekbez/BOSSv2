"""Shared error summarization utilities for mini-app network errors.

Provides a consistent, user-friendly short description to display on the screen
instead of long raw Requests exception messages.
"""
from __future__ import annotations
from typing import Optional

def summarize_error(err: Exception, max_len: int = 60) -> str:
    """Return a concise human-readable summary for a network exception.

    Strategy:
    1. Map common requests exception patterns to short phrases.
    2. Fallback to str(err) or exception class name.
    3. Trim to max_len preserving meaning.
    """
    import requests  # type: ignore

    # Direct class-based mappings
    if isinstance(err, requests.exceptions.Timeout):
        msg = "Timeout"
    elif isinstance(err, requests.exceptions.ConnectTimeout):
        msg = "Connect timeout"
    elif isinstance(err, requests.exceptions.ReadTimeout):
        msg = "Read timeout"
    elif isinstance(err, requests.exceptions.SSLError):
        msg = "TLS/SSL error"
    elif isinstance(err, requests.exceptions.TooManyRedirects):
        msg = "Too many redirects"
    elif isinstance(err, requests.exceptions.HTTPError):
        resp = getattr(err, 'response', None)
        if resp is not None:
            reason = getattr(resp, 'reason', '') or ''
            msg = f"HTTP {resp.status_code} {reason}".strip()
        else:
            msg = "HTTP error"
    elif isinstance(err, requests.exceptions.ConnectionError):
        raw = str(err)
        if 'Name or service not known' in raw or 'nodename nor servname provided' in raw or 'Temporary failure in name resolution' in raw:
            msg = 'DNS failure'
        elif 'Failed to establish a new connection' in raw or 'NewConnectionError' in raw:
            msg = 'Connection failed'
        elif 'Connection refused' in raw:
            msg = 'Connection refused'
        else:
            msg = 'Connection error'
    else:
        # Generic fallback
        raw = str(err) or err.__class__.__name__
        # Pattern-based cleanup for common verbose requests text
        if 'HTTPSConnectionPool' in raw or 'HTTPConnectionPool' in raw:
            if 'Max retries exceeded' in raw:
                if 'Read timed out' in raw:
                    msg = 'Read timeout'
                elif 'Connect timeout' in raw:
                    msg = 'Connect timeout'
                else:
                    msg = 'Max retries (network)'
            else:
                msg = 'Connection pool error'
        else:
            msg = raw

    if len(msg) > max_len:
        msg = msg[: max_len - 3] + '...'
    return msg
