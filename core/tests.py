from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.checkin_access import MAX_FAILED_ATTEMPTS
from core.models import ContestSettings, Organization, Participant, Team

PIN = "4821"


def set_pin(pin):
    ContestSettings.objects.update_or_create(pk=1, defaults={"checkin_pin": pin})


def make_team(username, name, is_onsite, members=("A",)):
    org, _ = Organization.objects.get_or_create(name="KBTU")
    team = Team.objects.create(
        owner=User.objects.create(username=username),
        name=name,
        organization=org,
        is_onsite=is_onsite,
        is_school_team=False,
        is_women_team=False,
    )
    for member in members:
        Participant.objects.create(team=team, full_name=member)
    return team


class CheckinTestBase(TestCase):
    def setUp(self):
        cache.clear()
        set_pin(PIN)
        self.onsite = make_team("u1", "Onsite Team", is_onsite=True)
        self.online = make_team("u2", "Online Team", is_onsite=False)
        self.empty = make_team("u3", "Empty Team", is_onsite=True, members=())

    def enter_pin(self, pin=PIN):
        return self.client.post(reverse("checkin"), {"pin": pin})

    def toggle(self, team):
        return self.client.post(reverse("checkin_toggle", args=[team.id]))


class CheckinPinTests(CheckinTestBase):
    def test_without_pin_shows_pin_form_and_no_teams(self):
        response = self.client.get(reverse("checkin"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="pin"')
        self.assertNotContains(response, "Onsite Team")

    def test_wrong_pin_is_rejected(self):
        response = self.enter_pin("0000")
        self.assertContains(response, "Неверный пин", status_code=200)
        self.assertNotContains(response, "Onsite Team")

    def test_correct_pin_unlocks_page(self):
        response = self.enter_pin()
        self.assertRedirects(response, reverse("checkin"))
        page = self.client.get(reverse("checkin"))
        self.assertContains(page, "Onsite Team")
        self.assertNotContains(page, "Online Team")
        self.assertNotContains(page, "Empty Team")

    def test_page_shows_team_and_member_counters(self):
        make_team("u4", "Second Onsite", is_onsite=True, members=("B", "C"))
        self.enter_pin()
        response = self.client.get(reverse("checkin"))
        self.assertEqual(response.context["total_members"], 3)
        self.assertEqual(response.context["arrived_members"], 0)
        self.toggle(Team.objects.get(name="Second Onsite"))
        response = self.client.get(reverse("checkin"))
        self.assertEqual(response.context["arrived_count"], 1)
        self.assertEqual(response.context["arrived_members"], 2)

    def test_too_many_wrong_attempts_block_even_correct_pin(self):
        for _ in range(MAX_FAILED_ATTEMPTS):
            self.enter_pin("0000")
        response = self.enter_pin()
        self.assertEqual(response.status_code, 429)
        self.assertNotContains(response, "Onsite Team", status_code=429)

    def test_staff_does_not_need_pin(self):
        User.objects.create_user("staff", password="pw", is_staff=True)
        self.client.login(username="staff", password="pw")
        self.assertContains(self.client.get(reverse("checkin")), "Onsite Team")

    def test_page_is_disabled_when_pin_not_configured(self):
        set_pin("")
        self.assertEqual(self.client.get(reverse("checkin")).status_code, 404)
        self.assertEqual(self.enter_pin("").status_code, 404)


class CheckinToggleTests(CheckinTestBase):
    def test_toggle_requires_pin(self):
        self.assertEqual(self.toggle(self.onsite).status_code, 403)
        self.onsite.refresh_from_db()
        self.assertIsNone(self.onsite.arrived_at)

    def test_toggle_marks_and_unmarks_arrival(self):
        self.enter_pin()

        first = self.toggle(self.onsite)
        self.assertTrue(first.json()["arrived"])
        self.onsite.refresh_from_db()
        self.assertIsNotNone(self.onsite.arrived_at)

        second = self.toggle(self.onsite)
        self.assertFalse(second.json()["arrived"])
        self.onsite.refresh_from_db()
        self.assertIsNone(self.onsite.arrived_at)

    def test_toggle_rejects_get(self):
        self.enter_pin()
        response = self.client.get(reverse("checkin_toggle", args=[self.onsite.id]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_online_or_unknown_team_returns_404(self):
        self.enter_pin()
        self.assertEqual(self.toggle(self.online).status_code, 404)
        missing = self.client.post(reverse("checkin_toggle", args=[999999]))
        self.assertEqual(missing.status_code, 404)


class LoginPrefixTests(TestCase):
    def setUp(self):
        cache.clear()
        self.team = make_team("lp", "Prefix Team", is_onsite=True)

    def test_default_prefix_keeps_existing_logins(self):
        self.assertEqual(self.team.login, f"kbtuspring26-{self.team.id}")

    def test_login_follows_prefix_from_config(self):
        settings = ContestSettings.load()
        settings.login_prefix_value = "kbtufall26-"
        settings.save()
        self.assertEqual(Team.objects.get(pk=self.team.pk).login, f"kbtufall26-{self.team.id}")

    def test_csv_upload_parses_login_with_dashes_in_prefix(self):
        from core.admin_views import team_id_from_login
        self.assertEqual(team_id_from_login("kbtu-fall-26-42"), 42)
        self.assertEqual(team_id_from_login("kbtuspring26-7"), 7)
        self.assertIsNone(team_id_from_login("garbage"))
