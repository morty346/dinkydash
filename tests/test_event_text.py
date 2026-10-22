"""Calendar descriptions cleaned for the wall."""

from dinkydash.event_text import (clean_description, description_lines,
                                  location_for_display)


class TestCleanDescription:
    def test_keeps_rehearsal_notes(self):
        raw = (
            "Section C — 2.5-2.11, pg 69-102, #32-50 (All Cast & Crew).\n"
            "5:00-6:00 Spot Work (as needed) - she may be held until 6:00."
        )
        assert "Section C" in clean_description(raw)
        assert "Spot Work" in clean_description(raw)

    def test_drops_zoom_boilerplate(self):
        raw = (
            "Bring trainers\n"
            "Join Zoom Meeting\n"
            "https://zoom.us/j/123456789\n"
            "Meeting ID: 123 456 789\n"
        )
        assert clean_description(raw) == "Bring trainers"

    def test_url_only_description_is_empty(self):
        assert clean_description("https://meet.google.com/abc-defg-hij") is None

    def test_unescapes_ical_newlines(self):
        assert clean_description("Line one\\nLine two") == "Line one\nLine two"


class TestLocationForDisplay:
    def test_keeps_a_school_name(self):
        assert location_for_display("Zumbrota-Mazeppa High School") == (
            "Zumbrota-Mazeppa High School", False)

    def test_hides_a_zoom_url(self):
        url = "https://us06web.zoom.us/j/123456789?pwd=abcdef"
        assert location_for_display(url) == (None, True)

    def test_hides_google_meet(self):
        assert location_for_display("https://meet.google.com/abc-defg-hij") == (
            None, True)


class TestDescriptionLines:
    def test_respects_disabled(self):
        assert description_lines("Hello", enabled=False) == []

    def test_clamps_long_text(self):
        long = "x" * 400
        lines = description_lines(long)
        assert len("".join(lines)) <= 280
