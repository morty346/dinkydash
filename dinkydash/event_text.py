"""Calendar text the wall can read without leaking join links.

Feeds put video-call URLs in LOCATION and boilerplate in DESCRIPTION. The raw
values stay in the payload; the dashboard calls here at render time.
"""

import re
from html import unescape

# Enough for a rehearsal call sheet; the fit script can still drop rows.
MAX_DESCRIPTION_CHARS = 200
MAX_DESCRIPTION_LINES = 2

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
_INVITE_OPENER = re.compile(
    r"\bis inviting you to\b.*\b(?:zoom|teams|google meet)\b|"
    r"^Microsoft Teams meeting\b|"
    r"^Join\s+(?:Zoom\s+Meeting|Microsoft Teams|Google Meet)\b",
    re.IGNORECASE,
)
_LABEL_LINE = re.compile(
    r"^(?:Join and take notes|Meeting chat link|Click here to join|"
    r"Join instructions|Join by SIP|One tap mobile|Dial by your location|"
    r"Google Meet joining info|Join on your computer.*)$",
    re.IGNORECASE,
)
_META_LINE = re.compile(
    r"^(?:Meeting ID|Passcode|Password|PIN|Conference ID|Video call link)"
    r"\s*[:：]?",
    re.IGNORECASE,
)
_PHONE_DIAL = re.compile(r"^\+[\d\s(),*#-]{12,}\s*(?:US|UK|Canada)?", re.IGNORECASE)
_SIP_LINE = re.compile(r"^•\s*\S+@zoomcrc\.com", re.IGNORECASE)
_SEPARATOR = re.compile(r"^[-─—]{3,}\s*$")


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


def _line_opens_conference(line):
    stripped = line.strip()
    if not stripped:
        return False
    if _INVITE_OPENER.search(stripped):
        return True
    if _VIDEO_HOST.search(stripped) and _URL.search(stripped):
        return True
    if stripped.lower().startswith("https://meet.google.com/"):
        return True
    return False


def _is_boilerplate_line(line):
    stripped = line.strip()
    if not stripped:
        return True
    if _URL.search(stripped):
        return True
    if _line_opens_conference(stripped):
        return True
    if _LABEL_LINE.match(stripped):
        return True
    if _META_LINE.match(stripped):
        return True
    if _PHONE_DIAL.match(stripped):
        return True
    if _SIP_LINE.match(stripped):
        return True
    if _SEPARATOR.match(stripped):
        return True
    if ",," in stripped and "#" in stripped and re.search(r"\d{3}", stripped):
        return True
    return False


def _entire_body_is_conference(text):
    if not (_VIDEO_HOST.search(text) or re.search(r"meet\.google\.com", text, re.I)):
        return False
    if re.search(
        r"Join Zoom|Meeting ID|is inviting you|teams\.microsoft|"
        r"meet\.google\.com",
        text,
        re.I,
    ):
        return True
    return False


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

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cut = len(lines)
    for index, line in enumerate(lines):
        if _line_opens_conference(line):
            cut = index
            break

    prefix = lines[:cut]
    if cut == len(lines) and _entire_body_is_conference(text):
        prefix = []

    kept = [line for line in prefix if not _is_boilerplate_line(line)]
    if not kept:
        return None
    return "\n".join(kept)


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
