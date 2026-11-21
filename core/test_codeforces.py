from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.codeforces import clean_team_name
from core.models import ContestSettings, Organization, Participant, Team


class CleanTeamNameTests(SimpleTestCase):
    def test_removes_emoji(self):
        self.assertEqual(clean_team_name("Котики 🥰🥰🥰"), "Котики")
        self.assertEqual(clean_team_name("⭐Stars⭐ ❤️ team 👨‍👩‍👧"), "Stars team")
        self.assertEqual(clean_team_name("Brand™ 👍🏽 ok"), "Brand ok")

    def test_keeps_letters_digits_and_programmer_punctuation(self):
        for name in ["O(DA^2)", "#include<hope>", "O(√n)", "Қанағат-2 & Co.", "len' dumat'", "iq: below zero"]:
            self.assertEqual(clean_team_name(name), name)

    def test_pipe_and_newlines_cannot_break_the_format(self):
        self.assertEqual(clean_team_name("a|b\nc"), "a/b c")

    def test_empty_after_cleaning(self):
        self.assertEqual(clean_team_name("🥰🥰", fallback="Team 7"), "Team 7")


def make_team(username, name, is_onsite, org="KBTU", members=("Ivanov Ivan",), **flags):
    organization, _ = Organization.objects.get_or_create(name=org)
    team = Team.objects.create(
        owner=User.objects.create(username=username), name=name, organization=organization,
        is_onsite=is_onsite, is_school_team=flags.get("school", False), is_women_team=flags.get("women", False),
    )
    for member in members:
        Participant.objects.create(team=team, full_name=member)
    return team


class CodeforcesLineTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_onsite_uses_contest_id_online_adds_o(self):
        onsite = make_team("1", "Котики 🥰🥰🥰", True, women=True)
        online = make_team("2", "Remote", False, members=("A B", "C D"))
        self.assertEqual(
            onsite.generate_cf_format("654321"),
            f"654321| {onsite.login} | {onsite.password} | KBTU: Котики[W] - Ivanov Ivan",
        )
        self.assertTrue(online.generate_cf_format("654321").startswith("654321o| "))
        self.assertTrue(online.generate_cf_format("654321").endswith("KBTU: Remote - A B,C D"))


class ExportActionTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_superuser("admin", "a@a.a", "pw")
        self.client.login(username="admin", password="pw")
        self.onsite = make_team("1", "On 🥰", True)
        self.online = make_team("2", "Off", False)
        self.empty = make_team("3", "Nobody", True, members=())

    def export(self):
        return self.client.post(reverse("admin:core_team_changelist"), {
            "action": "export_as_codeforces_format",
            "_selected_action": [self.onsite.pk, self.online.pk, self.empty.pk],
        }, follow=True)

    def test_downloads_file_with_contest_ids(self):
        settings = ContestSettings.load()
        settings.codeforces_contest_id = "654321"
        settings.save()
        response = self.export()
        self.assertIn("attachment", response["Content-Disposition"])
        lines = response.content.decode().splitlines()
        self.assertEqual(len(lines), 2)  # team without members is skipped
        self.assertTrue(lines[0].startswith("654321| ") and lines[0].endswith("KBTU: On - Ivanov Ivan"))
        self.assertTrue(lines[1].startswith("654321o| "))

    def test_without_contest_id_shows_error(self):
        response = self.export()
        self.assertContains(response, "Codeforces contest id")
        self.assertNotIn("attachment", response.get("Content-Disposition", ""))
