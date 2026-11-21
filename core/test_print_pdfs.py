import re

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.models import ContestSettings, Organization, Participant, Team
from core.print_pdfs import PrintTexts, Slip, TeamCard, password_slips_pdf, seat_number, team_cards_pdf

TEXTS = PrintTexts(
    title="KBTU Open Fall 2026",
    place_date="Almaty, KBTU, November 22, 2026",
    contest_url="https://kbtuopen26.contest.codeforces.com/",
)


def page_count(pdf):
    return len(re.findall(rb"/Type /Page\b", pdf))


def slip(i, room=2, seat=None, team="Team", org="KBTU"):
    return Slip(team=f"{team} {i}", organization=org, login=f"kbtufall26-{i}", password="Ab3xK9mQ2z",
                room=room, seat=seat if seat is not None else i)


class PasswordSlipsTests(SimpleTestCase):
    def test_six_slips_per_page(self):
        for count, pages in ((1, 1), (6, 1), (7, 2), (250, 42)):
            pdf = password_slips_pdf([slip(i) for i in range(count)], TEXTS)
            self.assertTrue(pdf.startswith(b"%PDF"))
            self.assertEqual(page_count(pdf), pages, count)

    def test_handles_kazakh_emoji_long_names_and_missing_seat(self):
        slips = [
            Slip("Қанағаттандырылмағандықтарыңыздан 🥰🥰", "SDU+KBTU+ЖЕНПУ", "kbtufall26-1", "pw", None, None),
            Slip("Attack on Contest: THE LAST ATTACK" * 3, "Tashkent University of Information Technologies",
                 "kbtufall26-2", "pw", 280, 1),
        ]
        self.assertEqual(page_count(password_slips_pdf(slips, TEXTS)), 1)

    def test_empty_list_gives_a_valid_pdf(self):
        self.assertTrue(password_slips_pdf([], TEXTS).startswith(b"%PDF"))


class TeamCardsTests(SimpleTestCase):
    def test_one_page_per_team(self):
        cards = [
            TeamCard("Nova", "IITU", ["Targyn Manas", "Orazbaev Madi"], 2, 1),
            TeamCard("Attack on Contest: THE LAST ATTACK", "Tashkent University of Information Technologies",
                     ["Mirokilov Davlatbek Sanjarovich", "Marufjonov Azizbek Husan ugli",
                      "Rahmatillayev Shohruh Jahongir ugli"], 280, 1),
            TeamCard("Котики 🥰", "КБТУ", [], None, None),
        ]
        pdf = team_cards_pdf(cards, TEXTS)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(page_count(pdf), 3)

    def test_seat_number(self):
        self.assertEqual(seat_number(7), "07")
        self.assertEqual(seat_number(30), "30")
        self.assertEqual(seat_number(None), "—")


def make_team(username, *, onsite=True, seat=None, status="accepted", members=("A B",)):
    org, _ = Organization.objects.get_or_create(name="KBTU")
    team = Team.objects.create(owner=User.objects.create(username=username), name=username, organization=org,
                               is_onsite=onsite, is_school_team=False, is_women_team=False, status=status, seat=seat)
    for member in members:
        Participant.objects.create(team=team, full_name=member)
    return team


class PrintViewsTests(TestCase):
    def setUp(self):
        cache.clear()
        make_team("a", seat="Room 364, seat 1")
        make_team("b", seat="Room 364, seat 30")
        make_team("c", seat="Room 2, seat 4")
        make_team("d")  # onsite without seat: gets a slip, no room sign
        make_team("online", onsite=False, seat="Room 2, seat 9")
        make_team("rejected", status="rejected", seat="Room 2, seat 10")
        make_team("empty", members=(), seat="Room 2, seat 11")
        User.objects.create_user("staff", password="pw", is_staff=True)

    def test_requires_staff(self):
        for name in ("print_passwords", "print_team_cards"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_passwords_pdf_download(self):
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("print_passwords"))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('filename="passwords.pdf"', response["Content-Disposition"])
        self.assertEqual(page_count(response.content), 1)  # 4 eligible teams -> one page

    def test_team_cards_one_page_per_eligible_team(self):
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("print_team_cards"))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('filename="team_cards.pdf"', response["Content-Disposition"])
        self.assertEqual(page_count(response.content), 4)  # a, b, c, d

    def test_texts_come_from_config(self):
        settings = ContestSettings.load()
        self.assertEqual(settings.contest_url, "https://kbtuopen26.contest.codeforces.com/")
        self.assertTrue(settings.print_title)
        self.assertTrue(settings.print_place_date)
