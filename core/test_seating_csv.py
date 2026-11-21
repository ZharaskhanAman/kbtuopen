import csv
import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import Organization, Participant, Room, Team


def make_team(username, org_name, is_onsite=True, status="pending", seat=None):
    org, _ = Organization.objects.get_or_create(name=org_name)
    team = Team.objects.create(
        owner=User.objects.create(username=username),
        name=username,
        organization=org,
        is_onsite=is_onsite,
        is_school_team=False,
        is_women_team=False,
        status=status,
        seat=seat,
    )
    Participant.objects.create(team=team, full_name=f"{username} member")
    return team


def read_csv(response):
    text = response.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def csv_file(rows, header=("Login", "Team", "Room", "Seat")):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(header)
    writer.writerows(rows)
    return SimpleUploadedFile("seating.csv", buffer.getvalue().encode("utf-8-sig"), content_type="text/csv")


class SeatingCsvBase(TestCase):
    def setUp(self):
        Room.objects.all().delete()
        Room.objects.create(number=101, capacity=4)
        Room.objects.create(number=102, capacity=3)
        Room.objects.create(number=103, capacity=5, is_active=False)
        self.a = make_team("a", "KBTU")
        self.b = make_team("b", "SDU", seat="Room 102, seat 2")
        self.c = make_team("c", "KBTU")
        self.online = make_team("o", "NU", is_onsite=False)
        User.objects.create_user("staff", password="pw", is_staff=True)
        self.client.login(username="staff", password="pw")

    def upload(self, rows, **kwargs):
        return self.client.post(
            reverse("seating_import"), {"csv_file": csv_file(rows, **kwargs)}, follow=True
        )


class SeatingExportTests(SeatingCsvBase):
    def test_requires_staff(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("seating_export")).status_code, 302)

    def test_plan_export_has_a_seat_for_every_eligible_team(self):
        rows = read_csv(self.client.get(reverse("seating_export")))
        self.assertEqual(sorted(r["Login"] for r in rows), sorted([self.a.login, self.b.login, self.c.login]))
        for row in rows:
            self.assertIn(row["Room"], {"101", "102"})
            self.assertTrue(row["Seat"].isdigit())
        self.a.refresh_from_db()
        self.assertIsNone(self.a.seat)

    def test_saved_export_reads_current_seats(self):
        rows = read_csv(self.client.get(reverse("seating_export") + "?source=saved"))
        by_login = {r["Login"]: r for r in rows}
        self.assertEqual((by_login[self.b.login]["Room"], by_login[self.b.login]["Seat"]), ("102", "2"))
        self.assertEqual((by_login[self.a.login]["Room"], by_login[self.a.login]["Seat"]), ("", ""))


class SeatingImportTests(SeatingCsvBase):
    def test_valid_file_saves_seats(self):
        response = self.upload([[self.a.login, "a", "101", "1"], [self.c.login, "c", "101", "3"]])
        self.assertContains(response, "Загружено мест: 2")
        self.a.refresh_from_db()
        self.c.refresh_from_db()
        self.assertEqual(self.a.seat, "Room 101, seat 1")
        self.assertEqual(self.c.seat, "Room 101, seat 3")

    def test_teams_missing_from_file_are_untouched(self):
        self.upload([[self.a.login, "a", "101", "1"]])
        self.b.refresh_from_db()
        self.assertEqual(self.b.seat, "Room 102, seat 2")

    def test_blank_rows_are_skipped(self):
        response = self.upload([[self.a.login, "a", "101", "1"], [self.c.login, "c", "", ""]])
        self.assertContains(response, "Загружено мест: 1")
        self.c.refresh_from_db()
        self.assertIsNone(self.c.seat)

    def test_import_reports_adjacent_same_university(self):
        response = self.upload([[self.a.login, "a", "101", "1"], [self.c.login, "c", "101", "2"]])
        self.assertContains(response, "соседей из одного вуза: 1")

    def assert_rejected(self, rows, message, **kwargs):
        response = self.upload(rows, **kwargs)
        self.assertContains(response, message)
        self.a.refresh_from_db()
        self.assertIsNone(self.a.seat)

    def test_any_error_saves_nothing(self):
        self.assert_rejected(
            [[self.a.login, "a", "101", "1"], [self.c.login, "c", "999", "1"]],
            "Строка 3: кабинет 999",
        )

    def test_seat_out_of_range(self):
        self.assert_rejected([[self.a.login, "a", "102", "4"]], "Строка 2: в кабинете 102 только 3 мест")

    def test_inactive_room(self):
        self.assert_rejected([[self.a.login, "a", "103", "1"]], "Строка 2: кабинет 103")

    def test_duplicate_seat(self):
        self.assert_rejected(
            [[self.a.login, "a", "101", "2"], [self.c.login, "c", "101", "2"]],
            "Строка 3: место Room 101, seat 2 уже занято (строка 2)",
        )

    def test_duplicate_team(self):
        self.assert_rejected(
            [[self.a.login, "a", "101", "1"], [self.a.login, "a", "101", "2"]],
            "Строка 3: команда",
        )

    def test_unknown_or_online_team(self):
        self.assert_rejected(
            [[self.a.login, "a", "101", "1"], ["kbtuspring26-999999", "x", "101", "2"]],
            "Строка 3: нет оффлайн-команды",
        )
        self.assert_rejected(
            [[self.a.login, "a", "101", "1"], [self.online.login, "o", "101", "2"]],
            "Строка 3: нет оффлайн-команды",
        )

    def test_bad_numbers(self):
        self.assert_rejected([[self.a.login, "a", "101", "x"]], "Строка 2: место должно быть числом")
        self.assert_rejected([["garbage", "a", "101", "1"]], "Строка 2: не понимаю логин")

    def test_missing_columns(self):
        self.assert_rejected([[self.a.login, "101"]], "нет колонок: Seat", header=("Login", "Room"))

    def test_comma_separated_file_is_accepted(self):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Login", "Room", "Seat"])
        writer.writerow([self.a.login, "101", "4"])
        upload = SimpleUploadedFile("s.csv", buffer.getvalue().encode("utf-8"), content_type="text/csv")
        self.client.post(reverse("seating_import"), {"csv_file": upload})
        self.a.refresh_from_db()
        self.assertEqual(self.a.seat, "Room 101, seat 4")


class SeatingImportByNameTests(SeatingCsvBase):
    HEADER = ("Login", "Team", "Organization", "Room", "Seat")

    def test_matches_by_team_and_organization_without_login(self):
        self.upload([["", "a", "kbtu", "101", "1"]], header=self.HEADER)
        self.a.refresh_from_db()
        self.assertEqual(self.a.seat, "Room 101, seat 1")

    def test_name_and_organization_win_over_a_foreign_login(self):
        # A file made on a copy of prod has different ids: trust name + org, not login.
        self.upload([[self.c.login, "a", "KBTU", "101", "2"]], header=self.HEADER)
        self.a.refresh_from_db()
        self.c.refresh_from_db()
        self.assertEqual(self.a.seat, "Room 101, seat 2")
        self.assertIsNone(self.c.seat)

    def test_unknown_name_and_organization_is_rejected(self):
        response = self.upload([["", "nope", "KBTU", "101", "1"]], header=self.HEADER)
        self.assertContains(response, "Строка 2: нет оффлайн-команды «nope» (KBTU)")

    def test_ambiguous_name_and_organization_is_rejected(self):
        make_team("twin", "KBTU")
        Team.objects.filter(name="twin").update(name="a")
        response = self.upload([["", "a", "KBTU", "101", "1"]], header=self.HEADER)
        self.assertContains(response, "Строка 2: несколько команд «a» (KBTU)")
        self.a.refresh_from_db()
        self.assertIsNone(self.a.seat)
