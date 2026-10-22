"""How this family writes a time of day.

One setting, one function, and every place that prints a time goes through it:
the agenda on the wall, the headline computed when a brief is stale, the times
handed to the model, and the line the settings page shows after testing a
calendar link. A family who reads `15:45` as a mistake reads all four of them.

Times are *stored* in one shape — `%H:%M`, with the event's full ISO `start`
beside it — and written for a reader at the point of display. That is what lets
the setting take effect on the next redraw rather than on the next calendar
fetch, and it keeps one shape in the store for both modes.
"""

from datetime import date, datetime, time

# The two ways a clock is read. `24h` stays the default: it is the house style,
# and it is what every dashboard already hanging on a wall shows.
CLOCKS = ("24h", "12h")
DEFAULT_CLOCK = "24h"


def clock_of(config):
    """Which clock this family reads. Anything unrecognised is 24-hour."""
    setting = (config or {}).get("clock")
    return setting if setting in CLOCKS else DEFAULT_CLOCK


def format_time(moment, clock=DEFAULT_CLOCK):
    """A time of day as this family writes it, or None if it cannot be read.

    Takes a `datetime`, a `time`, or a string holding either — which is what
    lets a caller pass an event's `start` and fall back to its `time`.
    """
    moment = _time_of(moment)
    if moment is None:
        return None
    if clock == "12h":
        # Built rather than strftime'd: `%-I` is glibc-specific and `%p` is
        # locale-dependent, and neither belongs in the one function every
        # displayed time goes through. Lowercase because the dashboard's voice
        # is quiet — `3:45 pm` sits beside a title without shouting.
        return f"{moment.hour % 12 or 12}:{moment.minute:02d} " \
               f"{'am' if moment.hour < 12 else 'pm'}"
    return f"{moment.hour:02d}:{moment.minute:02d}"


def format_time_range(start, end, clock=DEFAULT_CLOCK):
    """A start and end on the same day, written as one column string."""
    start_text = format_time(start, clock)
    end_text = format_time(end, clock)
    if not start_text:
        return end_text
    if not end_text or start_text == end_text:
        return start_text
    if clock == "12h":
        start_moment = _time_of(start)
        end_moment = _time_of(end)
        if start_moment and end_moment:
            same_half = (start_moment.hour < 12) == (end_moment.hour < 12)
            if same_half:
                suffix = " am" if end_moment.hour < 12 else " pm"
                start_bit = f"{start_moment.hour % 12 or 12}:{start_moment.minute:02d}"
                end_bit = f"{end_moment.hour % 12 or 12}:{end_moment.minute:02d}"
                return f"{start_bit}–{end_bit}{suffix}"
    return f"{start_text}–{end_text}"


def format_all_day_through(last_day):
    """How many days an all-day block runs, for the time column."""
    if last_day is None:
        return None
    if isinstance(last_day, str):
        try:
            last_day = date.fromisoformat(last_day)
        except ValueError:
            return None
    return last_day.strftime("%-d %b")


def _time_of(value):
    """The hour and minute in `value`, whatever shape it arrived in."""
    if isinstance(value, (datetime, time)):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    for parse in (datetime.fromisoformat, time.fromisoformat):
        try:
            return parse(text)
        except (TypeError, ValueError):
            continue
    return None
