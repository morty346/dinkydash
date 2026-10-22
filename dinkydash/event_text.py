"""Calendar text the wall can read without leaking join links.

Feeds put video-call URLs in LOCATION and boilerplate in DESCRIPTION. The raw
values stay in the payload; the dashboard calls here at render time.
"""

import re
from html import unescape

# Enough for a rehearsal call sheet; the fit script can still drop rows.
MAX_DESCRIPTION_CHARS = 280
MAX_DESCRIPTION_LINES = 4

_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_VIDEO_HOST = re.compile(
    r"(?:^|[./@])(?:"
    r"[\w.-]*zoom\.us|"
    r"meet\.google\.com|"
    r"teams\.microsoft\.com|"
    r"teams\.live\.com|"
    r"[\w.-]*webex\.com|"
    r"gotomeeting\.com|"
    r"gotomeet\.me|"
    r"bluejeans\.com|"
    r"whereby\.com|"
    r"meet\.jit\.si"
    r")(?:/|$|\?)",
    re.IGNORECASE,
)
_MEETING_LINE = re.compile(
    r"^(?:"
    r".*zoom\s+meeting.*|"
    r".*join\s+(?:zoom|google\s+meet|microsoft\s+teams|teams)\b.*|"
    r".*\bmeet\.google\.com/\S+.*|"
    r".*\bteams\.microsoft\.com/\S+.*|"
    r".*https?://\S*zoom\.us/\S+.*|"
    r".*passcode:.*|"
    r".*meeting\s+id:.*|"
    r".*dial(?:-|\s)?in.*|"
    r".*one\s+tap\s+mobile.*|"
    r".*────────.*|"
    r".*──────────.*"
    r")$",
    re.IGNORECASE,
)


def _normalise_newlines(text):
    text = text.replace("\\n", "\n").replace("\\N", "\n")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _looks_like_url(text):
    stripped = text.strip()
    if stripped.lower().startswith(("http://", "https://", "www.")):
        return True
    return bool(_URL.fullmatch(stripped))


def location_for_display(raw):
    """A physical place to show, and whether the meeting is online-only.

    Returns `(label, is_online)`. When `is_online` is true and `label` is None,
    the template shows a compact Online marker instead of a URL.
    """
    if raw is None:
        return None, False
    text = _normalise_newlines(str(raw)).strip()
    if not text:
        return None, False

    if _VIDEO_HOST.search(text) or (_looks_like_url(text) and _URL.search(text)):
        remainder = _URL.sub("", text).strip(" \t,;—–-|")
        if remainder and not _VIDEO_HOST.search(remainder):
            return remainder, False
        return None, True

    if _looks_like_url(text):
        return None, True

    if _URL.search(text):
        remainder = _URL.sub("", text).strip(" \t,;—–-|")
        if remainder:
            return remainder, False
        return None, True

    return text, False


def _strip_html(text):
    """Drop tags without interpreting entities as structure."""
    without = re.sub(r"<[^>]+>", " ", text)
    return unescape(without)


def clean_description(raw):
    """A DESCRIPTION worth showing, or None if nothing useful remains."""
    if raw is None:
        return None
    text = _normalise_newlines(str(raw).strip())
    if not text:
        return None
    if text.startswith("<") and ">" in text:
        text = _strip_html(text)
    text = _normalise_newlines(text).strip()
    if not text:
        return None

    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if _MEETING_LINE.match(stripped):
            continue
        without_urls = _URL.sub("", stripped).strip(" \t-–—|,")
        if not without_urls:
            continue
        lines.append(stripped)

    if not lines:
        return None

    joined = "\n".join(lines)
    if _URL.sub("", joined).strip(" \t-–—|,") == "":
        return None
    return joined


def description_lines(raw, *, enabled=True):
    """At most a few lines, clamped, for the template to escape."""
    if not enabled:
        return []
    text = clean_description(raw)
    if not text:
        return []
    lines = text.split("\n")
    kept = []
    length = 0
    for line in lines:
        if len(kept) >= MAX_DESCRIPTION_LINES:
            break
        if length + len(line) > MAX_DESCRIPTION_CHARS and kept:
            break
        room = MAX_DESCRIPTION_CHARS - length
        if len(line) > room:
            if room <= 1:
                break
            line = line[: room - 1].rstrip() + "…"
        kept.append(line)
        length += len(line)
    return kept
