from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from core.models import Organization, Team
from core.telegram import build_credentials_message, build_online_message, needs_laptop


class CredentialsMessageTests(SimpleTestCase):
    def test_has_login_room_and_seat_but_no_password(self):
        text = build_credentials_message("kbtuspring26-7", "Room 365, seat 4", "SDU")
        self.assertIn("Login: kbtuspring26-7", text)
        self.assertIn("Room: 365", text)
        self.assertIn("Seat: 4", text)
        self.assertNotIn("Password", text)
        self.assertNotIn("laptop", text)

    def test_kbtu_teams_are_told_to_bring_laptops(self):
        text = build_credentials_message("kbtuspring26-7", "Room 444, seat 1", "KBTU")
        self.assertIn("bring your own laptop", text)
        self.assertIn("ноутбук", text)

    def test_joint_and_cyrillic_kbtu_count(self):
        self.assertTrue(needs_laptop("SDU + KBTU"))
        self.assertTrue(needs_laptop("КБТУ"))
        self.assertFalse(needs_laptop("IITU"))

    def test_without_seat_there_is_no_room_line(self):
        text = build_credentials_message("kbtuspring26-7", None, "SDU")
        self.assertNotIn("Room", text)

    def test_hand_written_seat_is_shown_as_is(self):
        text = build_credentials_message("kbtuspring26-7", "у окна", "SDU")
        self.assertIn("Seat: у окна", text)


class OnlineMessageTests(SimpleTestCase):
    def test_online_message_has_login_and_password_only(self):
        text = build_online_message("kbtuspring26-9", "s3cret")
        self.assertIn("Login: kbtuspring26-9", text)
        self.assertIn("Password: s3cret", text)
        self.assertIn("Contest link:", text)
        self.assertNotIn("Room", text)
        self.assertNotIn("laptop", text)


class SendCredentialsTests(TestCase):
    @mock.patch("core.models.send_message", return_value=(200, "ok"))
    def test_team_sends_message_without_password(self, send):
        org = Organization.objects.create(name="KBTU")
        team = Team.objects.create(
            owner=User.objects.create(username="12345"), name="t", organization=org,
            is_onsite=True, is_school_team=False, is_women_team=False, seat="Room 444, seat 2",
        )
        team.send_credentials_by_telegram()
        chat_id, text = send.call_args.args
        self.assertEqual(chat_id, "12345")
        self.assertNotIn(team.password, text)
        self.assertIn("Room: 444", text)
        self.assertIn("bring your own laptop", text)
        team.refresh_from_db()
        self.assertIsNotNone(team.password_sent_at)

    @mock.patch("core.models.send_message", return_value=(200, "ok"))
    def test_online_team_gets_password(self, send):
        org = Organization.objects.create(name="KBTU")
        team = Team.objects.create(
            owner=User.objects.create(username="777"), name="online", organization=org,
            is_onsite=False, is_school_team=False, is_women_team=False,
        )
        team.send_credentials_by_telegram()
        _, text = send.call_args.args
        self.assertIn(f"Password: {team.password}", text)
        self.assertNotIn("laptop", text)
