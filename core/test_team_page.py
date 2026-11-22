from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from core.models import ContestSettings, Organization, Team


def accepted_team(username, *, onsite):
    org, _ = Organization.objects.get_or_create(name="KBTU")
    user = User.objects.create_user(username, password="pw")
    team = Team.objects.create(owner=user, name=username, organization=org, is_onsite=onsite,
                               is_school_team=False, is_women_team=False, status="accepted",
                               seat="Room 2, seat 1" if onsite else None)
    return user, team


class TeamPageTests(TestCase):
    def setUp(self):
        cache.clear()
        ContestSettings.load()

    def test_onsite_team_page_hides_password(self):
        _, team = accepted_team("onsite", onsite=True)
        self.client.login(username="onsite", password="pw")
        html = self.client.get(reverse("team")).content.decode()
        self.assertIn(team.login, html)
        self.assertNotIn(team.password, html)
        self.assertNotIn("Password", html)

    def test_online_team_page_still_shows_password(self):
        _, team = accepted_team("online", onsite=False)
        self.client.login(username="online", password="pw")
        self.assertIn(team.password, self.client.get(reverse("team")).content.decode())
