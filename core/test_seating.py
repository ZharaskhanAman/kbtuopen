from collections import Counter

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.models import Organization, Participant, Room, Team
from core.seating import (
    NotEnoughSeats,
    RoomSpec,
    SeatingTeam,
    allocate_quotas,
    count_adjacent_conflicts,
    org_tokens,
    plan_seating,
    spread_positions,
)


def teams_from(orgs):
    return [SeatingTeam(id=i + 1, name=f"T{i + 1}", organization=org) for i, org in enumerate(orgs)]


class OrgTokensTests(SimpleTestCase):
    def test_splits_combined_organizations(self):
        self.assertEqual(org_tokens("KBTU + IITU"), {"kbtu", "iitu"})
        self.assertEqual(org_tokens("SDU+KBTU+ЖЕНПУ"), {"sdu", "kbtu", "женпу"})

    def test_normalizes_case_and_spaces(self):
        self.assertEqual(org_tokens("  Satbayev   University "), {"satbayev university"})


class AllocationTests(SimpleTestCase):
    def test_quotas_are_proportional_to_capacity(self):
        rooms = [RoomSpec(1, 30), RoomSpec(2, 10), RoomSpec(3, 20)]
        quotas = dict(allocate_quotas(30, rooms))
        self.assertEqual(quotas, {1: 15, 2: 5, 3: 10})
        self.assertEqual(sum(quotas.values()), 30)

    def test_rooms_without_capacity_are_skipped(self):
        quotas = dict(allocate_quotas(3, [RoomSpec(1, 0), RoomSpec(2, 5)]))
        self.assertEqual(quotas, {2: 3})

    def test_not_enough_seats_raises(self):
        with self.assertRaises(NotEnoughSeats):
            allocate_quotas(11, [RoomSpec(1, 5), RoomSpec(2, 5)])

    def test_spread_positions_leave_gaps(self):
        self.assertEqual(spread_positions(3, 9), [1, 4, 7])
        self.assertEqual(spread_positions(4, 4), [1, 2, 3, 4])


class PlanSeatingTests(SimpleTestCase):
    def test_every_team_gets_a_unique_seat_within_capacity(self):
        teams = teams_from(["KBTU"] * 20 + ["SDU"] * 7 + ["IITU"] * 5 + ["РФМШ"] * 8)
        rooms = [RoomSpec(2, 31), RoomSpec(258, 12), RoomSpec(280, 7), RoomSpec(365, 21)]
        plan = plan_seating(teams, rooms)

        self.assertEqual(sorted(a.team.id for a in plan), [t.id for t in teams])
        self.assertEqual(len({(a.room, a.position) for a in plan}), len(plan))
        capacity = {r.number: r.capacity for r in rooms}
        for assignment in plan:
            self.assertTrue(1 <= assignment.position <= capacity[assignment.room])

    def test_same_university_never_adjacent_in_full_room(self):
        teams = teams_from(["KBTU", "KBTU", "KBTU", "SDU", "IITU", "SDU"])
        plan = plan_seating(teams, [RoomSpec(5, 6)])
        self.assertEqual(count_adjacent_conflicts(plan), 0)

    def test_combined_organization_counts_as_same_university(self):
        teams = teams_from(["KBTU", "KBTU + IITU", "SDU", "NU"])
        plan = plan_seating(teams, [RoomSpec(5, 4)])
        by_position = {a.position: a.team.organization for a in plan}
        for pos in range(1, 4):
            pair = {by_position[pos], by_position[pos + 1]}
            self.assertNotEqual(pair, {"KBTU", "KBTU + IITU"})

    def test_big_university_is_spread_across_rooms(self):
        teams = teams_from(["KBTU"] * 12 + ["SDU"] * 12)
        rooms = [RoomSpec(1, 20), RoomSpec(2, 20), RoomSpec(3, 20)]
        plan = plan_seating(teams, rooms)
        kbtu_per_room = Counter(a.room for a in plan if a.team.organization == "KBTU")
        self.assertEqual(sorted(kbtu_per_room.values()), [4, 4, 4])

    def test_plan_is_deterministic(self):
        teams = teams_from(["KBTU", "SDU", "KBTU", "NU", "IITU", "KBTU"])
        rooms = [RoomSpec(1, 4), RoomSpec(2, 4)]
        self.assertEqual(plan_seating(teams, rooms), plan_seating(teams, rooms))

    def test_seat_label(self):
        plan = plan_seating(teams_from(["KBTU"]), [RoomSpec(365, 1)])
        self.assertEqual(plan[0].label, "Room 365, seat 1")


def make_team(username, org_name, is_onsite=True, status="pending", members=("A",)):
    org, _ = Organization.objects.get_or_create(name=org_name)
    team = Team.objects.create(
        owner=User.objects.create(username=username),
        name=username,
        organization=org,
        is_onsite=is_onsite,
        is_school_team=False,
        is_women_team=False,
        status=status,
    )
    for member in members:
        Participant.objects.create(team=team, full_name=member)
    return team


class SeatingViewTests(TestCase):
    def setUp(self):
        Room.objects.all().delete()
        Room.objects.create(number=101, capacity=4)
        Room.objects.create(number=102, capacity=0)
        self.kbtu1 = make_team("k1", "KBTU")
        self.kbtu2 = make_team("k2", "KBTU", status="accepted")
        self.sdu = make_team("s1", "SDU")
        self.online = make_team("o1", "KBTU", is_onsite=False)
        self.rejected = make_team("r1", "KBTU", status="rejected")
        self.empty = make_team("e1", "NU", members=())
        User.objects.create_user("staff", password="pw", is_staff=True)

    def test_requires_staff(self):
        self.assertEqual(self.client.get(reverse("seating")).status_code, 302)

    def test_preview_does_not_save(self):
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("seating") + "?preview=1")
        self.assertContains(response, "Room 101")
        self.kbtu1.refresh_from_db()
        self.assertIsNone(self.kbtu1.seat)

    def test_preview_shows_people_and_computers_per_room(self):
        Room.objects.filter(number=101).update(computers=9)
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("seating") + "?preview=1")
        self.assertContains(response, "Room 101 · 3 / 4 команд · 3 чел. · пришли 0 · 9 комп.")
        self.assertContains(response, "<th>Чел.</th>")
        self.assertContains(response, "<td>1</td>")
        self.assertEqual(response.context["people_count"], 3)

    def test_page_shows_saved_seating_not_preview_by_default(self):
        self.client.login(username="staff", password="pw")
        empty = self.client.get(reverse("seating"))
        self.assertContains(empty, "Места ещё не распределены")
        self.assertNotContains(empty, "Room 101 ·")

        self.client.post(reverse("seating"))
        saved = self.client.get(reverse("seating"))
        self.assertNotContains(saved, "Места ещё не распределены")
        self.assertContains(saved, "Сохранённая рассадка")
        self.assertContains(saved, "Room 101 · 3 / 4 команд")

    def test_shows_who_has_arrived(self):
        from django.utils import timezone
        Team.objects.filter(pk=self.kbtu1.pk).update(arrived_at=timezone.now())
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("seating") + "?preview=1")
        self.assertEqual(response.context["arrived_count"], 1)
        self.assertContains(response, "пришли 1 ·")
        self.assertContains(response, 'class="arrived-yes"', count=1)
        self.assertContains(response, 'class="arrived-no"', count=2)

    def test_saved_view_lists_teams_without_seat(self):
        Team.objects.filter(pk=self.kbtu1.pk).update(seat="Room 101, seat 1")
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("seating"))
        self.assertContains(response, "Без места: 2")

    def test_save_assigns_seats_only_to_eligible_teams(self):
        self.client.login(username="staff", password="pw")
        response = self.client.post(reverse("seating"))
        self.assertRedirects(response, reverse("seating"))

        seats = {t.name: t.seat for t in Team.objects.all()}
        for name in ("k1", "k2", "s1"):
            self.assertTrue(seats[name].startswith("Room 101, seat "))
        for name in ("o1", "r1", "e1"):
            self.assertIsNone(seats[name])
        self.assertEqual(len({seats["k1"], seats["k2"], seats["s1"]}), 3)

    def test_listed_strong_team_is_not_seated_in_lecture_hall(self):
        Room.objects.filter(number=101).update(is_lecture=True)
        Room.objects.create(number=103, capacity=4)
        Team.objects.filter(pk=self.sdu.pk).update(name="And yet they burn out")
        self.client.login(username="staff", password="pw")
        response = self.client.get(reverse("seating") + "?preview=1")
        self.assertContains(response, "★")
        self.assertContains(response, "не найдены среди рассаживаемых команд (7 из 8)")
        self.client.post(reverse("seating"))
        self.sdu.refresh_from_db()
        self.assertTrue(self.sdu.seat.startswith("Room 103, "))

    def test_save_with_not_enough_seats_shows_error(self):
        Room.objects.filter(number=101).update(capacity=2)
        self.client.login(username="staff", password="pw")
        response = self.client.post(reverse("seating"), follow=True)
        self.assertContains(response, "Не хватает мест")
        self.kbtu1.refresh_from_db()
        self.assertIsNone(self.kbtu1.seat)


class DedicatedRoomTests(SimpleTestCase):
    def test_dedicated_room_takes_only_pure_university_teams(self):
        teams = teams_from(["KBTU"] * 5 + ["KBTU + IITU", "SDU", "NU"])
        rooms = [RoomSpec(444, 3, only="KBTU"), RoomSpec(1, 10)]
        plan = plan_seating(teams, rooms)

        in_444 = [a.team.organization for a in plan if a.room == 444]
        self.assertEqual(in_444, ["KBTU"] * 3)
        self.assertEqual(sorted(a.position for a in plan if a.room == 444), [1, 2, 3])
        self.assertEqual(len(plan), len(teams))
        joint = next(a for a in plan if a.team.organization == "KBTU + IITU")
        self.assertEqual(joint.room, 1)

    def test_dedicated_room_with_fewer_teams_is_partly_filled(self):
        plan = plan_seating(teams_from(["KBTU", "SDU"]), [RoomSpec(444, 30, only="KBTU"), RoomSpec(1, 5)])
        self.assertEqual([a.team.organization for a in plan if a.room == 444], ["KBTU"])

    def test_capacity_check_counts_only_teams_left_for_open_rooms(self):
        teams = teams_from(["KBTU"] * 4 + ["SDU"] * 2)
        plan = plan_seating(teams, [RoomSpec(444, 4, only="KBTU"), RoomSpec(1, 2)])
        self.assertEqual(len(plan), 6)
        with self.assertRaises(NotEnoughSeats):
            plan_seating(teams, [RoomSpec(444, 3, only="KBTU"), RoomSpec(1, 2)])

    def test_conflicts_in_ignored_rooms_are_not_counted(self):
        plan = plan_seating(teams_from(["KBTU"] * 3), [RoomSpec(444, 3, only="KBTU")])
        self.assertEqual(count_adjacent_conflicts(plan), 2)
        self.assertEqual(count_adjacent_conflicts(plan, ignore_rooms={444}), 0)


def strong_teams_from(orgs, strong_ids):
    return [
        SeatingTeam(id=i + 1, name=f"T{i + 1}", organization=org, strong=(i + 1) in strong_ids)
        for i, org in enumerate(orgs)
    ]


class StrongTeamTests(SimpleTestCase):
    ROOMS = [
        RoomSpec(444, 10, only="KBTU", lecture=True),
        RoomSpec(161, 10, lecture=True),
        RoomSpec(269, 10),
        RoomSpec(365, 10),
    ]

    def test_strong_teams_never_sit_in_lecture_halls(self):
        teams = strong_teams_from(["KBTU"] * 12 + ["SDU"] * 8, strong_ids={1, 2, 3, 13})
        plan = plan_seating(teams, self.ROOMS)
        self.assertEqual(len(plan), 20)
        strong_rooms = {a.room for a in plan if a.team.strong}
        self.assertTrue(strong_rooms <= {269, 365}, strong_rooms)

    def test_strong_teams_are_spread_between_regular_rooms(self):
        teams = strong_teams_from(["SDU", "NU", "IITU", "AITU"] * 4, strong_ids={1, 2, 3, 4})
        plan = plan_seating(teams, self.ROOMS)
        per_room = Counter(a.room for a in plan if a.team.strong)
        self.assertEqual(sorted(per_room.values()), [2, 2])

    def test_too_many_strong_teams_for_regular_rooms(self):
        teams = strong_teams_from(["SDU"] * 6, strong_ids={1, 2, 3, 4, 5})
        rooms = [RoomSpec(161, 10, lecture=True), RoomSpec(269, 2)]
        with self.assertRaises(NotEnoughSeats):
            plan_seating(teams, rooms)
