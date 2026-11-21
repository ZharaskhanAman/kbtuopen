from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import ContestSettings


class AdminUiTests(TestCase):
    def setUp(self):
        User.objects.create_superuser("admin", "a@a.a", "pw")
        self.client.login(username="admin", password="pw")

    def test_settings_list_opens_the_single_settings_form(self):
        response = self.client.get(reverse("admin:core_contestsettings_changelist"))
        self.assertRedirects(response, reverse("admin:core_contestsettings_change", args=[1]))
        self.assertEqual(str(ContestSettings.load()), "Настройки соревнования")

    def test_settings_form_is_grouped(self):
        response = self.client.get(reverse("admin:core_contestsettings_changelist"), follow=True)
        for section in ("Регистрация и check-in", "Логины и Codeforces", "Печать и Telegram"):
            self.assertContains(response, section)

    def test_team_tools_are_a_separate_bar_not_object_tools(self):
        response = self.client.get(reverse("admin:core_team_changelist"))
        html = response.content.decode()
        tools = html[html.index('class="object-tools"'):]
        tools = tools[: tools.index("</ul>")]
        self.assertNotIn("print/passwords.pdf", tools)  # only "Add team" stays up there
        self.assertIn('class="team-tools"', html)
        for url in ("seating", "checkin", "print_passwords", "print_team_cards", "export-teams-onsite", "upload-csv"):
            self.assertIn(f'href="{reverse(url)}"', html)
