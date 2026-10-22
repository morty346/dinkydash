"""Full video-call invite bodies must not reach the wall."""

from dinkydash.event_text import clean_description, description_lines

ZOOM_BODY = """\
Alex Example is inviting you to a scheduled Zoom meeting.

Join Zoom Meeting
https://us06web.zoom.us/j/87105096525?pwd=FAKEPWD0000000000000000

Join and take notes
https://us06web.zoom.us/j/87105096525?pwd=FAKEPWD0000000000000000&mynotes=on

Meeting chat link
https://us06web.zoom.us/launch/jc/87105096525

Meeting ID: 871 0509 6525
Passcode: 230768

---

One tap mobile
+13126266799,,87105096525#,,,,*230768# US (Chicago)
+16469313860,,87105096525#,,,,*230768# US


---

Join by SIP
• 87105096525@zoomcrc.com

Join instructions
https://us06web.zoom.us/meetings/87105096525/invitations?signature=fake
"""

MEET_BODY = """\
Google Meet joining info

Video call link: https://meet.google.com/abc-defg-hij
Or dial: +1 555-010-2030 PIN: 123 456 789#
"""

TEAMS_BODY = """\
Microsoft Teams meeting

Join on your computer, mobile app or room device
https://teams.microsoft.com/l/meetup-join/19%3ameeting_fake%40thread.v2/0

Meeting ID: 395 185 221 02
Passcode: 7aB9cD
"""


class TestConferenceInvites:
    def test_a_full_zoom_invite_leaves_no_notes(self):
        assert clean_description(ZOOM_BODY) is None
        assert description_lines(ZOOM_BODY) == []

    def test_human_text_before_a_zoom_block_is_kept(self):
        raw = "Bring trainers and water.\n\n" + ZOOM_BODY
        assert clean_description(raw) == "Bring trainers and water."

    def test_a_google_meet_invite_leaves_no_notes(self):
        assert clean_description(MEET_BODY) is None

    def test_a_teams_invite_leaves_no_notes(self):
        assert clean_description(TEAMS_BODY) is None

    def test_notes_are_capped_at_two_lines(self):
        raw = "\n".join(f"Line {index}" for index in range(6))
        assert len(description_lines(raw)) == 2
